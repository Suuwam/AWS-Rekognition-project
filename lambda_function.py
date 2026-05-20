import json
import boto3
import base64
import uuid
import traceback

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

BUCKET_NAME = 'my-rekognition-images-12345'  # ← CHANGE THIS

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}

def lambda_handler(event, context):
    # Handle browser preflight
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'POST')
    if http_method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}
    
    try:
        # Parse body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        # Extract image
        image_data = body.get('image', '')
        if not image_data:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'No image field in JSON body'})}
        
        # Strip data:image prefix
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Invalid base64 image data'})}
        
        if len(image_bytes) < 100:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Image file too small or empty'})}
        
        # Upload to S3
        filename = f"uploads/{uuid.uuid4()}.jpg"
        s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=image_bytes, ContentType='image/jpeg')
        
        # Rekognition - labels with bounding boxes
        labels_resp = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': filename}},
            MaxLabels=25,
            MinConfidence=60
        )
        
        # Rekognition - text with bounding boxes
        text_resp = rekognition.detect_text(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': filename}}
        )
        
        # Format labels
        labels = []
        for label in labels_resp['Labels']:
            instances = []
            for inst in label.get('Instances', []):
                bb = inst.get('BoundingBox', {})
                if bb:
                    instances.append({
                        'left': round(bb.get('Left', 0), 4),
                        'top': round(bb.get('Top', 0), 4),
                        'width': round(bb.get('Width', 0), 4),
                        'height': round(bb.get('Height', 0), 4)
                    })
            labels.append({
                'name': label['Name'],
                'confidence': round(label['Confidence'], 1),
                'instances': instances,
                'parents': [p['Name'] for p in label.get('Parents', [])]
            })
        
        # Format text
        texts = []
        for t in text_resp.get('TextDetections', []):
            bb = t.get('Geometry', {}).get('BoundingBox', {})
            texts.append({
                'text': t['DetectedText'],
                'confidence': round(t['Confidence'], 1),
                'type': t['Type'],
                'box': {
                    'left': round(bb.get('Left', 0), 4),
                    'top': round(bb.get('Top', 0), 4),
                    'width': round(bb.get('Width', 0), 4),
                    'height': round(bb.get('Height', 0), 4)
                } if bb else None
            })
        
        # Pre-signed URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'imageUrl': url,
                'labels': labels,
                'texts': texts
            })
        }
        
    except Exception as e:
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': str(e)})
        }

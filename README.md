#  AWS Rekognition

> A serverless image recognition app that detects objects, text, and faces in two images simultaneously — then compares the results visually with transparent bounding boxes.
>
> **Built as a beginner AWS project. Evolved from a broken single-image prototype into a side-by-side comparison tool.**

[![AWS](https://img.shields.io/badge/AWS-Serverless-orange?logo=amazon-aws)](https://aws.amazon.com)
[![Free Tier](https://img.shields.io/badge/Free%20Tier-Eligible-success)](https://aws.amazon.com/free)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)

<img width="1289" height="670" alt="Screenshot From 2026-05-20 13-36-33" src="https://github.com/user-attachments/assets/9bd9be79-88f7-419b-84c3-654752dac951" />

---

##  Project Evolution (What Changed Along the Way)

This project didn't start as a side-by-side comparison tool. It evolved through **two major versions** and several painful debugging sessions.

### Version 1: Single Image Upload
The original idea was simple: upload one image, detect labels, show results. Basic stack:
- S3 for image storage
- Lambda to process
- API Gateway to connect frontend
- Rekognition for AI

**What worked:** The architecture was sound and fully serverless.

**What didn't:**
-  "Failed to fetch" errors everywhere
-  CORS nightmare — browser blocked every API call
-  Lambda couldn't see the image data (`event['body']` was empty)
-  Dark opaque bounding boxes completely covered the people in photos

### Version 2: Side-by-Side Comparison (Current)
After fixing the foundational bugs, I rebuilt the frontend with:
-  **Two image panels** side-by-side (horizontal layout)
-  **Single "Analyze Both" button** instead of separate buttons per panel
-  **Transparent bounding boxes** — 6% opacity fill + glowing borders so you can actually see the photos
-  **Click-to-toggle labels** — click any chip to hide/show just that object's boxes
-  **Auto-comparison engine** — JavaScript compares Image A vs Image B labels instantly
-  **Rounded rectangle boxes** instead of sharp corners

---

##  What I Struggled On (And How I Fixed It)

### 1. "Failed to Fetch" — The CORS + Lambda Proxy Trap
**The error:** Every browser request failed with `TypeError: Failed to fetch`.

**Root cause:** API Gateway was **NOT** using Lambda Proxy Integration. Without it, the `event` object reaching Lambda has no `body` key. My Lambda looked for `event['body']`, found nothing, and returned `"Error: No image"`.

**The fix:**
1. Go to API Gateway → Resources → `/analyze` → POST → Integration Request
2. Check **"Use Lambda Proxy Integration"**
3. **Redeploy the API** (Actions → Deploy API → prod)
4. Every. Single. Time. You. Change. Anything.

>  **Lesson:** If you see "No image" but you definitely sent one, check Proxy Integration first. Don't waste 2 hours debugging Lambda when the problem is API Gateway.

### 2. Can't Edit Files Directly in S3
**The confusion:** I kept trying to edit `index.html` inside the S3 console like Google Docs.

**The reality:** S3 is **object storage**, not a file editor. You cannot open a file, change one line, and save. You must:
1. Download the file
2. Edit locally
3. Re-upload the entire file (overwrite)

>  **Lesson:** S3 is a warehouse, not a workspace. Treat it like FTP — upload complete files only.

### 3. Bounding Boxes Hiding the Images
**The problem:** The first version of bounding boxes used 12% opacity fill. On group photos with many people, the boxes turned into solid colored sheets that completely hid faces.

**The evolution:**
| Attempt | Fill Opacity | Result |
|---------|-------------|--------|
| v1 | 12% solid | Couldn't see faces |
| v2 | 6% + glow shadow | Perfect visibility |

**The fix:**
```javascript
ctx.fillStyle = 'hsla(hue, 90%, 60%, 0.06)';  // 6% opacity
ctx.shadowColor = color;
ctx.shadowBlur = 12;  // glow effect
ctx.lineWidth = 2.5;  // visible border
```

### 4. Two Buttons vs One Button
**Original design:** Each panel had its own "Analyze" button. Users had to click twice.

**User feedback:** "Only one button."

**The fix:** Single "Analyze Both Images" button at the center bottom. It dynamically changes text based on what's uploaded:
- Both images present → "Analyze Both Images"
- Only Image A → "Analyze Image A"
- Only Image B → "Analyze Image B"

### 5. Mixed HTTP/HTTPS Content
**The issue:** S3 static website uses `http://`. API Gateway uses `https://`. Some browsers block the request.

---

##  What I Learned

### Technical Lessons
1. **Lambda Proxy Integration is non-negotiable** for REST APIs with JSON payloads
2. **Rekognition bounding boxes are normalized** (0.0–1.0 ratios), not pixels. Multiply by `canvas.width` and `canvas.height` to draw correctly.
3. **Pre-signed URLs** are the secure pattern for showing private S3 images in a browser — no public buckets needed.
4. **Canvas overlay resolution** must match `img.naturalWidth/Height`, not CSS display size, or boxes drift on resize.
5. **API Gateway CORS** requires redeployment after every change. Just enabling it isn't enough.

### Architecture Lessons
1. **Serverless is faster to debug** when you know where to look. CloudWatch Logs became my best friend.
2. **IAM Roles > API Keys**. Never put credentials in frontend code. The Lambda execution role handles all AWS permissions securely.
3. **One Lambda, one responsibility**. My Lambda does exactly 3 things: decode image, store in S3, call Rekognition. Nothing more.
4. **Client-side rendering is powerful**. All comparison logic, box drawing, and toggling happens in the browser. The backend just returns raw data.

### Process Lessons
1. **Start simple, then compare.** Building the single-image version first taught me the data flow. Adding the second image was just duplication.
2. **Visual feedback matters.** Transparent boxes aren't a "nice to have" — they're essential. If users can't see the photo, the AI results are useless.
3. **Free Tier is generous.** I processed 50+ images during development and my bill is still $0.00.
---

### Services Used

| Layer | Service | Purpose |
|-------|---------|---------|
| **Frontend** | S3 Static Website | Hosts `index.html` (no server) |
| **API** | API Gateway | REST endpoint with CORS + Lambda Proxy |
| **Compute** | AWS Lambda | Decodes images, calls AI, returns JSON |
| **AI** | Amazon Rekognition | Detects labels, text, bounding boxes |
| **Storage** | Amazon S3 | Stores uploaded images privately |
| **Security** | AWS IAM | Execution role — zero hardcoded keys |
| **Monitoring** | CloudWatch | Lambda logs & metrics |

---

##  Quick Start

### Prerequisites
- AWS Account (Free Tier eligible)
- AWS CLI (optional, for uploads)

### 1. Create S3 Buckets

```bash
# Frontend bucket (public static website)
aws s3 mb s3://my-rekognition-frontend-12345
aws s3 website s3://my-rekognition-frontend-12345 --index-document index.html

# Image storage bucket (private)
aws s3 mb s3://my-rekognition-images-12345
```

### 2. Create IAM Role for Lambda

Attach these managed policies:
- `AmazonRekognitionFullAccess`
- `AmazonS3FullAccess` (or scoped custom policy)
- `AWSLambdaBasicExecutionRole`

### 3. Deploy Lambda Function

1. Go to **AWS Console → Lambda → Create function**
2. Runtime: `Python 3.11`
3. Timeout: `30 seconds`
4. Memory: `512 MB`
5. Paste code from [`lambda_function.py`](lambda/lambda_function.py)
6. Update `BUCKET_NAME` variable

### 4. Create API Gateway

1. **API Gateway → Create API → REST API**
2. Create resource `/analyze`
3. Create **POST** method → Lambda integration
4. **Enable Lambda Proxy Integration** (critical!)
5. **Enable CORS** (POST + OPTIONS)
6. **Deploy API** to stage `prod`
7. Copy the **Invoke URL**

### 5. Deploy Frontend

```bash
# Edit index.html — replace API_URL with your Invoke URL
# Then upload to S3 (remember: you cannot edit in S3 directly!)
aws s3 cp index.html s3://my-rekognition-frontend-12345/ --acl public-read
```

Open your S3 static website endpoint and test!

---

##  Project Structure

```
aws-rekognition-compare/
├── frontend/
│   └── index.html              # Single-page app (HTML/CSS/JS)
├── lambda/
│   └── lambda_function.py      # Python backend handler
├── docs/
│   └── architecture.png        # Architecture diagram
└── README.md                   # This file
```

---

##  API Reference

### `POST /analyze`

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
  "success": true,
  "imageUrl": "https://s3.amazonaws.com/...",
  "labels": [
    {
      "name": "Person",
      "confidence": 99.4,
      "instances": [
        { "left": 0.12, "top": 0.34, "width": 0.23, "height": 0.45 }
      ],
      "parents": ["Human"]
    }
  ],
  "texts": [
    {
      "text": "Hello",
      "confidence": 98.5,
      "type": "WORD",
      "box": { "left": 0.5, "top": 0.2, "width": 0.1, "height": 0.05 }
    }
  ]
}
```

---

##  Frontend Features

| Feature | Implementation |
|---------|---------------|
| Drag & Drop | Native HTML5 Drag API |
| Image Preview | FileReader API → Base64 |
| Bounding Boxes | HTML5 Canvas overlay on `<img>` |
| Transparent Boxes | `rgba()` fill at 6% opacity + glow shadow |
| Label Tags | Floating pills above each box |
| Toggle Visibility | Click label chips to filter |
| Comparison | JavaScript `Set` intersection/difference |

---

## Security

-  **No AWS credentials in frontend** — all AWS calls happen inside Lambda via IAM Role
-  **Private S3 images** — browser receives time-limited pre-signed URLs (1 hour expiry)
-  **CORS restricted** — API Gateway only accepts requests from your domain
-  **Input validation** — Lambda validates image format and size before processing
-  **API Gateway payload limit** — 10MB max prevents abuse

---

##  Future Improvements

- [ ] Add **Amazon Cognito** for user authentication
- [ ] Store history in **DynamoDB**
- [ ] Add **face comparison** between Image A and Image B
- [ ] Deploy via **CloudFront** for HTTPS + custom domain (skipped Step 7!)
- [ ] Add **image resizing** client-side before upload (reduce payload)
- [ ] **Batch processing** — analyze entire albums at once

---

##  License

MIT License — feel free to use, fork, and build on this.

---

##  Connect

Built this as a beginner AWS project. If you found it helpful, give it a sTAR and share your own serverless builds!

##  Appendix

<img width="869" height="648" alt="Screenshot From 2026-05-20 12-28-43" src="https://github.com/user-attachments/assets/7217076e-fefd-428a-997a-dccbaecb9d32" />
<img width="870" height="778" alt="Screenshot From 2026-05-20 12-30-45" src="https://github.com/user-attachments/assets/7ed7a9fb-10af-402a-8d94-48ca14fa3793" />
<img width="811" height="997" alt="Screenshot From 2026-05-20 12-38-18" src="https://github.com/user-attachments/assets/0281b698-f1fc-41f7-854a-016bfb4b6d58" />
<img width="786" height="972" alt="Screenshot From 2026-05-20 12-42-35" src="https://github.com/user-attachments/assets/34d2d70e-26f8-4770-8814-aeaaf23d8da2" />
<img width="879" height="579" alt="Screenshot From 2026-05-20 12-47-58" src="https://github.com/user-attachments/assets/d35a6ee4-ba43-48f6-8ae2-5553cc5e342c" />
<img width="878" height="960" alt="Screenshot From 2026-05-20 13-02-01" src="https://github.com/user-attachments/assets/a3679a79-5660-4a6f-ac13-c89a003ca820" />
<img width="878" height="956" alt="Screenshot From 2026-05-20 13-07-54" src="https://github.com/user-attachments/assets/d3d6f13f-5db9-4d0f-a41a-d8f0b8c7400a" />
<img width="870" height="603" alt="Screenshot From 2026-05-20 12-40-41" src="https://github.com/user-attachments/assets/4c745894-dbd6-4a1c-80aa-d7f09948c0e7" />
<img width="582" height="630" alt="Screenshot From 2026-05-20 12-40-53" src="https://github.com/user-attachments/assets/70769082-006e-41b1-a01a-18296e061fd7" />
<img width="863" height="432" alt="Screenshot From 2026-05-20 12-41-08" src="https://github.com/user-attachments/assets/5c475e23-1780-4a6d-8e88-3cb6d295a151" />
<img width="577" height="262" alt="Screenshot From 2026-05-20 12-41-29" src="https://github.com/user-attachments/assets/186c5741-3249-4a75-a8c0-b3a5048f8b95" />



**#AWS #Serverless #Rekognition #CloudComputing #Python #JavaScript**

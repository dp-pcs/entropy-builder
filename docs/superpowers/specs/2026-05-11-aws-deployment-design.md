# Entropy AWS Deployment Design

**Date:** 2026-05-11
**Repo:** `dp-pcs/entropy-builder`
**Target URL:** `https://entropy.elelem.expert`
**AWS Region:** `us-east-1`

---

## Goal

Deploy the Entropy FastAPI web app to AWS using ECS Fargate (web + worker), with SQS decoupling the wizard submission from the 2-hour pipeline, S3 for job state and vault storage, and automated deploys from GitHub Actions on every push to `main`.

---

## Architecture

```
GitHub (dp-pcs/entropy-builder)
    │
    └── GitHub Actions (push to main)
           │ docker build → ECR push
           │ ecs update-service (web + worker)
           ▼
        ECR: entropy-builder (tagged by git SHA)

Route 53: entropy.elelem.expert → ALB (A alias)
ACM: SSL cert for entropy.elelem.expert
ALB: HTTPS 443 → web ECS tasks on port 8000

ECS Cluster: entropy-cluster
    ├── Web Service (1–2 tasks, 0.5 vCPU / 1 GB)
    │       FastAPI + uvicorn
    │       POST /api/wizard/submit → enqueue SQS
    │
    └── Worker Service (1–5 tasks, 2 vCPU / 8 GB)
            SQS long-poll → run_pipeline_job()
            Auto-scales on queue depth

SQS: entropy-jobs (standard queue, DLQ after 3 attempts)

S3: entropy-jobs-{aws-account-id}
    ├── uploads/{session_id}/{filename}     ← wizard file uploads
    ├── jobs/{job_id}/state.json            ← pipeline progress
    ├── jobs/{job_id}/entropy-vault.zip     ← completed vault
    └── jobs/{job_id}/claude_settings.json  ← MCP config

Secrets Manager:
    entropy/NOTION_TOKEN
    entropy/FIREWORKS_API_KEY
    entropy/GOOGLE_CLIENT_ID
    entropy/GOOGLE_CLIENT_SECRET
```

---

## Networking

**VPC:** `entropy-vpc` (`10.0.0.0/16`)
- 2 public subnets: `entropy-public-1a` (`10.0.1.0/24`), `entropy-public-1b` (`10.0.2.0/24`)
- Internet gateway attached
- No private subnets, no NAT gateway — all outbound calls (Notion, Gmail, Fireworks, read.ai) go direct

**Security Groups:**

| Name | Inbound | Outbound |
|------|---------|----------|
| `entropy-alb-sg` | 80, 443 from `0.0.0.0/0` | all |
| `entropy-web-sg` | 8000 from `entropy-alb-sg` only | all |
| `entropy-worker-sg` | none | all (SQS + S3 + external APIs) |

---

## DNS + SSL

1. ACM: request public cert for `entropy.elelem.expert` with DNS validation
2. Route 53: add CNAME validation record (ACM provides it)
3. ALB: HTTPS listener on 443 with the ACM cert; HTTP listener on 80 redirects to HTTPS
4. Route 53: A record `entropy.elelem.expert` → ALB DNS name (alias)

**Google OAuth redirect URIs** (set in Google Cloud Console):
- `https://entropy.elelem.expert/oauth/google/callback`
- `http://localhost:8000/oauth/google/callback`

**Authorized JavaScript origins:**
- `https://entropy.elelem.expert`
- `http://localhost:8000`

---

## ECR

Repository name: `entropy-builder`
Image tagged by git SHA: `{account}.dkr.ecr.us-east-1.amazonaws.com/entropy-builder:{sha}`

Both web and worker services use the same image. Entry point is set by ECS task definition `command` override:
- Web: `["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]`
- Worker: `["python", "-m", "worker"]`

---

## ECS

**Cluster:** `entropy-cluster` (Fargate launch type)

### Web Service

| Setting | Value |
|---------|-------|
| Task CPU | 0.5 vCPU |
| Task memory | 1 GB |
| Desired count | 1 |
| Max count | 2 |
| Health check | `GET /health` → 200 |
| Port | 8000 |

### Worker Service

| Setting | Value |
|---------|-------|
| Task CPU | 2 vCPU |
| Task memory | 8 GB |
| Desired count | 1 |
| Max count | 5 |
| Scale-out trigger | SQS `ApproximateNumberOfMessagesVisible` ≥ 1 |
| Scale-in trigger | SQS queue empty for 5 minutes |

### IAM Task Execution Role

Both services share a task execution role with:
- `ecr:GetAuthorizationToken`, `ecr:BatchGetImage` (pull image)
- `logs:CreateLogGroup`, `logs:PutLogEvents` (CloudWatch)
- `secretsmanager:GetSecretValue` for `entropy/*` (read secrets)
- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `entropy-jobs-*`
- `sqs:SendMessage`, `sqs:ReceiveMessage`, `sqs:DeleteMessage` on `entropy-jobs`

### Environment Variables (injected from Secrets Manager)

```
S3_BUCKET=entropy-jobs-{account-id}
AWS_REGION=us-east-1
BASE_URL=https://entropy.elelem.expert
NOTION_TOKEN={from Secrets Manager: entropy/NOTION_TOKEN}
FIREWORKS_API_KEY={from Secrets Manager: entropy/FIREWORKS_API_KEY}
GOOGLE_CLIENT_ID={from Secrets Manager: entropy/GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET={from Secrets Manager: entropy/GOOGLE_CLIENT_SECRET}
ENTROPY_TEMPLATE_PATH=/app/entropy-template
```

---

## SQS

**Queue name:** `entropy-jobs`
**Type:** Standard (at-least-once delivery)
**Visibility timeout:** 3 hours (longer than the ~2-hour pipeline)
**Message retention:** 4 days
**Dead-letter queue:** `entropy-jobs-dlq`, max receive count: 3

**Message body** (JSON):
```json
{
  "job_id": "uuid",
  "config": { ...JobConfig fields except credentials... },
  "s3_keys": ["uploads/session-id/file.pdf"]
}
```

Credentials (Google tokens, read.ai key) are stored in S3 job state at submission time and read by the worker from S3 — they are never put in the SQS message body.

---

## S3

**Bucket name:** `entropy-jobs-{aws-account-id}`

Lifecycle rules:
- `uploads/*`: expire after 7 days
- `jobs/*/entropy-vault.zip`: expire after 7 days
- `jobs/*/claude_settings.json`: expire after 7 days
- `jobs/*/state.json`: expire after 30 days

Server-side encryption: AES256 (already applied in `s3.py`).
Block all public access: enabled.

---

## Secrets Manager

| Secret name | Value |
|-------------|-------|
| `entropy/NOTION_TOKEN` | Shared internal token used by pipeline only |
| `entropy/FIREWORKS_API_KEY` | Shared Fireworks API key |
| `entropy/GOOGLE_CLIENT_ID` | OAuth app client ID |
| `entropy/GOOGLE_CLIENT_SECRET` | OAuth app client secret |

These are never included in user-facing outputs (vault, `claude_settings.json`).

---

## Code Changes Required

### 1. `webapp/jobs.py` — SQS enqueue instead of thread

`create_job()` enqueues to SQS instead of spawning `threading.Thread`. Credentials (Google tokens, read.ai key) are written to S3 job state before enqueueing so the worker can retrieve them.

```python
# Before (thread-based):
thread = threading.Thread(target=run_pipeline_job, args=(...), daemon=True)
thread.start()

# After (SQS-based):
sqs_client.send_message(
    QueueUrl=settings.sqs_queue_url,
    MessageBody=json.dumps({"job_id": job_id, "config": config_dict, "s3_keys": s3_keys})
)
```

### 2. New `worker.py` — SQS long-poll loop

Top-level module (`python -m worker`) that polls `entropy-jobs` and calls `run_pipeline_job()`.

```python
while True:
    messages = sqs.receive_message(QueueUrl=..., WaitTimeSeconds=20, MaxNumberOfMessages=1)
    for msg in messages.get("Messages", []):
        body = json.loads(msg["Body"])
        run_pipeline_job(body["job_id"], body["config"], body["s3_keys"])
        sqs.delete_message(QueueUrl=..., ReceiptHandle=msg["ReceiptHandle"])
```

On exception: log error, do NOT delete message (SQS retries up to 3x, then DLQ).

### 3. `webapp/jobs.py` → `generate_claude_settings()`

Remove Notion from the generated `claude_settings.json`. Users connect Notion via Claude Desktop → Connections → Install Notion. Only Gmail and read.ai remain in the file.

### 4. `webapp/templates/status.html` — setup guide update

4-step setup guide:
1. Install Obsidian, open vault
2. Install Claude Desktop, place `claude_settings.json`
3. Claude Desktop → Connections → Install Notion
4. Ask "What's the state of my portfolio?"

### 5. `Dockerfile`

Single image. `ENTROPY_TEMPLATE_PATH` points to `/app/entropy-template`. The `entropy` repo is added as a git submodule at `entropy-template/` inside `entropy-builder` — this makes it available in the Docker build context.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# entropy-template/ is the entropy repo git submodule, already in build context
ENV ENTROPY_TEMPLATE_PATH=/app/entropy-template
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6. `config.py` — add SQS queue URL

```python
sqs_queue_url: str = field(default_factory=lambda: os.environ.get("SQS_QUEUE_URL", ""))
```

---

## GitHub Actions

**File:** `.github/workflows/deploy.yml`
**Trigger:** push to `main`

Steps:
1. Configure AWS credentials (via `aws-actions/configure-aws-credentials` using GitHub OIDC — no long-lived access keys)
2. Log in to ECR
3. Build Docker image, tag with git SHA
4. Push to ECR
5. Update ECS web service (force new deployment)
6. Update ECS worker service (force new deployment)

**GitHub secrets required:**
```
AWS_ROLE_ARN    ← IAM role for GitHub OIDC (new, net-new)
```

No `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` — GitHub OIDC is more secure.

---

## What Is NOT Touched

- Existing `elelem.expert` Route 53 hosted zone (we only add one A record)
- Any existing EC2 instances, ECS clusters, S3 buckets, or other resources in the account
- Existing Synapse deployment

---

## Entropy Template Path

The pipeline requires the Obsidian vault template at `ENTROPY_TEMPLATE_PATH=/app/entropy-template`. The `entropy` repo (`dp-pcs/entropy` or `trilogy-group/entropy`) is added as a git submodule at `entropy-template/` inside `entropy-builder`. GitHub Actions checks out submodules (`submodules: true`) so the template is present at build time. The submodule is pinned to a specific commit so deploys are reproducible.

---

## Local Testing

Before deploying to AWS, run locally with:

```bash
# .env
S3_BUCKET=entropy-jobs-local        # use LocalStack or real bucket
AWS_REGION=us-east-1
BASE_URL=http://localhost:8000
NOTION_TOKEN=...
FIREWORKS_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ENTROPY_TEMPLATE_PATH=/Users/davidproctor/Documents/GitHub/entropy

uvicorn webapp.main:app --reload
```

For SQS locally, use [LocalStack](https://github.com/localstack/localstack) or a real SQS queue in your AWS account.

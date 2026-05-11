# Entropy AWS Infrastructure + GitHub Actions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision all AWS infrastructure for Entropy (VPC, S3, Secrets Manager, SQS, ECR, ECS Fargate web + worker, ALB, ACM, Route 53) and wire up automated GitHub Actions deployments via OIDC.

**Architecture:** All resources are net-new in `us-east-1`. Nothing touches existing account resources. The `elelem.expert` Route 53 hosted zone gets one new A record. GitHub Actions authenticates to AWS via OIDC (no long-lived access keys).

**Tech Stack:** AWS CLI v2, GitHub Actions, Docker (ECR push).

**Prerequisites:**
- AWS CLI configured: `aws configure` with credentials that have AdministratorAccess or equivalent (net-new resources only)
- `aws sts get-caller-identity` returns your account ID
- Docker installed and running
- App changes plan (`2026-05-11-aws-app-changes.md`) completed and merged to `main`

---

## File Map

```
entropy-builder/
└── .github/
    └── workflows/
        └── deploy.yml      NEW — GitHub Actions deploy workflow
```

No Terraform. All resources provisioned via AWS CLI. Commands use shell variables — set them once at the top of each task.

---

## Task 1: S3 bucket + lifecycle rules

**Resources:**
- S3 bucket: `entropy-jobs-{ACCOUNT_ID}`

- [ ] **Step 1: Set variables**

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="entropy-jobs-${ACCOUNT_ID}"
REGION="us-east-1"
echo "Bucket: $BUCKET"
```

- [ ] **Step 2: Create bucket**

```bash
aws s3api create-bucket \
  --bucket "$BUCKET" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION"
```

Expected: `{"Location": "http://entropy-jobs-....s3.amazonaws.com/"}`

Note: if region is `us-east-1`, omit `--create-bucket-configuration` (us-east-1 is the default):

```bash
aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
```

- [ ] **Step 3: Block all public access**

```bash
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

- [ ] **Step 4: Enable server-side encryption by default**

```bash
aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'
```

- [ ] **Step 5: Add lifecycle rules**

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "expire-uploads",
        "Filter": {"Prefix": "uploads/"},
        "Status": "Enabled",
        "Expiration": {"Days": 7}
      },
      {
        "ID": "expire-vaults",
        "Filter": {"Prefix": "jobs/"},
        "Status": "Enabled",
        "Expiration": {"Days": 30},
        "NoncurrentVersionExpiration": {"NoncurrentDays": 7}
      }
    ]
  }'
```

- [ ] **Step 6: Verify**

```bash
aws s3api get-bucket-encryption --bucket "$BUCKET" --query 'ServerSideEncryptionConfiguration'
aws s3api get-public-access-block --bucket "$BUCKET"
```

Expected: encryption AES256 enabled, all public access blocked.

---

## Task 2: Secrets Manager

**Resources:**
- `entropy/NOTION_TOKEN`
- `entropy/FIREWORKS_API_KEY`
- `entropy/GOOGLE_CLIENT_ID`
- `entropy/GOOGLE_CLIENT_SECRET`

Values come from your `.env` file in the entropy-builder repo.

- [ ] **Step 1: Create secrets (replace placeholder values with real values from .env)**

```bash
aws secretsmanager create-secret \
  --name "entropy/NOTION_TOKEN" \
  --secret-string "YOUR_NOTION_TOKEN" \
  --region us-east-1

aws secretsmanager create-secret \
  --name "entropy/FIREWORKS_API_KEY" \
  --secret-string "YOUR_FIREWORKS_API_KEY" \
  --region us-east-1

aws secretsmanager create-secret \
  --name "entropy/GOOGLE_CLIENT_ID" \
  --secret-string "YOUR_GOOGLE_CLIENT_ID" \
  --region us-east-1

aws secretsmanager create-secret \
  --name "entropy/GOOGLE_CLIENT_SECRET" \
  --secret-string "YOUR_GOOGLE_CLIENT_SECRET" \
  --region us-east-1
```

Expected: each returns `{"ARN": "arn:aws:secretsmanager:...", "Name": "entropy/..."}`

- [ ] **Step 2: Verify all four secrets exist**

```bash
aws secretsmanager list-secrets \
  --filter Key=name,Values=entropy/ \
  --query 'SecretList[].Name' \
  --output table
```

Expected: 4 rows — entropy/NOTION_TOKEN, entropy/FIREWORKS_API_KEY, entropy/GOOGLE_CLIENT_ID, entropy/GOOGLE_CLIENT_SECRET.

---

## Task 3: SQS queue + dead-letter queue

**Resources:**
- `entropy-jobs-dlq` (DLQ)
- `entropy-jobs` (main queue, routes to DLQ after 3 failures)

- [ ] **Step 1: Create DLQ**

```bash
DLQ_URL=$(aws sqs create-queue \
  --queue-name entropy-jobs-dlq \
  --region us-east-1 \
  --query QueueUrl --output text)
echo "DLQ: $DLQ_URL"

DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names QueueArn \
  --query Attributes.QueueArn --output text)
echo "DLQ ARN: $DLQ_ARN"
```

- [ ] **Step 2: Create main queue with DLQ and 3-hour visibility timeout**

```bash
QUEUE_URL=$(aws sqs create-queue \
  --queue-name entropy-jobs \
  --region us-east-1 \
  --attributes "{
    \"VisibilityTimeout\": \"10800\",
    \"MessageRetentionPeriod\": \"345600\",
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
  }" \
  --query QueueUrl --output text)
echo "Queue: $QUEUE_URL"
```

- [ ] **Step 3: Verify**

```bash
aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names VisibilityTimeout RedrivePolicy MessageRetentionPeriod
```

Expected: VisibilityTimeout=10800, RedrivePolicy contains DLQ ARN.

---

## Task 4: VPC + networking + security groups

**Resources:**
- VPC `entropy-vpc`
- 2 public subnets (us-east-1a, us-east-1b)
- Internet gateway
- Route table
- 3 security groups (ALB, web, worker)

- [ ] **Step 1: Create VPC**

```bash
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --region us-east-1 \
  --query Vpc.VpcId --output text)
aws ec2 create-tags --resources "$VPC_ID" --tags Key=Name,Value=entropy-vpc
echo "VPC: $VPC_ID"
```

- [ ] **Step 2: Create subnets**

```bash
SUBNET_1A=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --query Subnet.SubnetId --output text)
aws ec2 create-tags --resources "$SUBNET_1A" --tags Key=Name,Value=entropy-public-1a

SUBNET_1B=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --query Subnet.SubnetId --output text)
aws ec2 create-tags --resources "$SUBNET_1B" --tags Key=Name,Value=entropy-public-1b

echo "Subnets: $SUBNET_1A $SUBNET_1B"
```

- [ ] **Step 3: Internet gateway + route table**

```bash
IGW_ID=$(aws ec2 create-internet-gateway \
  --query InternetGateway.InternetGatewayId --output text)
aws ec2 attach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID"
aws ec2 create-tags --resources "$IGW_ID" --tags Key=Name,Value=entropy-igw

RTB_ID=$(aws ec2 create-route-table --vpc-id "$VPC_ID" \
  --query RouteTable.RouteTableId --output text)
aws ec2 create-route --route-table-id "$RTB_ID" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$IGW_ID"
aws ec2 associate-route-table --route-table-id "$RTB_ID" --subnet-id "$SUBNET_1A"
aws ec2 associate-route-table --route-table-id "$RTB_ID" --subnet-id "$SUBNET_1B"
```

- [ ] **Step 4: Security groups**

```bash
# ALB security group
ALB_SG=$(aws ec2 create-security-group \
  --group-name entropy-alb-sg \
  --description "Entropy ALB - public HTTPS" \
  --vpc-id "$VPC_ID" \
  --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id "$ALB_SG" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$ALB_SG" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Web ECS security group — inbound only from ALB
WEB_SG=$(aws ec2 create-security-group \
  --group-name entropy-web-sg \
  --description "Entropy web ECS tasks" \
  --vpc-id "$VPC_ID" \
  --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id "$WEB_SG" \
  --protocol tcp --port 8000 --source-group "$ALB_SG"

# Worker ECS security group — no inbound
WORKER_SG=$(aws ec2 create-security-group \
  --group-name entropy-worker-sg \
  --description "Entropy worker ECS tasks - outbound only" \
  --vpc-id "$VPC_ID" \
  --query GroupId --output text)

echo "SGs: ALB=$ALB_SG WEB=$WEB_SG WORKER=$WORKER_SG"
```

- [ ] **Step 5: Verify**

```bash
aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'SecurityGroups[].GroupName' --output table
```

Expected: entropy-alb-sg, entropy-web-sg, entropy-worker-sg (plus default).

---

## Task 5: ACM certificate + Route 53 record

**Resources:**
- ACM cert for `entropy.elelem.expert`
- Route 53 CNAME validation record in existing `elelem.expert` hosted zone
- Route 53 A record `entropy.elelem.expert` → ALB (done in Task 8 after ALB is created)

- [ ] **Step 1: Get the elelem.expert hosted zone ID**

```bash
ZONE_ID=$(aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='elelem.expert.'].Id" \
  --output text | sed 's|/hostedzone/||')
echo "Zone ID: $ZONE_ID"
```

Expected: a hosted zone ID like `Z1ABC2DEF3GHI`.

- [ ] **Step 2: Request ACM certificate**

```bash
CERT_ARN=$(aws acm request-certificate \
  --domain-name entropy.elelem.expert \
  --validation-method DNS \
  --region us-east-1 \
  --query CertificateArn --output text)
echo "Cert ARN: $CERT_ARN"
```

- [ ] **Step 3: Get the DNS validation record**

```bash
aws acm describe-certificate \
  --certificate-arn "$CERT_ARN" \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'
```

Expected output like:
```json
{"Name": "_abc123.entropy.elelem.expert.", "Type": "CNAME", "Value": "_xyz.acm-validations.aws."}
```

Save the `Name` and `Value` values.

- [ ] **Step 4: Add CNAME validation record to Route 53**

Replace `CNAME_NAME` and `CNAME_VALUE` with the values from Step 3:

```bash
CNAME_NAME="_abc123.entropy.elelem.expert."
CNAME_VALUE="_xyz.acm-validations.aws."

aws route53 change-resource-record-sets \
  --hosted-zone-id "$ZONE_ID" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"CREATE\",
      \"ResourceRecordSet\": {
        \"Name\": \"${CNAME_NAME}\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{\"Value\": \"${CNAME_VALUE}\"}]
      }
    }]
  }"
```

- [ ] **Step 5: Wait for certificate to be issued (up to 5 minutes)**

```bash
aws acm wait certificate-validated \
  --certificate-arn "$CERT_ARN" \
  --region us-east-1
echo "Certificate issued"
```

---

## Task 6: ECR repository + IAM roles

**Resources:**
- ECR repository: `entropy-builder`
- IAM role: `entropy-task-execution-role` (ECS task execution)
- IAM role: `entropy-github-actions-role` (GitHub OIDC)

- [ ] **Step 1: Create ECR repository**

```bash
aws ecr create-repository \
  --repository-name entropy-builder \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

ECR_URI="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/entropy-builder"
echo "ECR: $ECR_URI"
```

- [ ] **Step 2: Create ECS task execution role**

```bash
aws iam create-role \
  --role-name entropy-task-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name entropy-task-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

- [ ] **Step 3: Add inline policy for S3, SQS, and Secrets Manager**

```bash
aws iam put-role-policy \
  --role-name entropy-task-execution-role \
  --policy-name entropy-task-policy \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [\"s3:GetObject\", \"s3:PutObject\", \"s3:DeleteObject\"],
        \"Resource\": \"arn:aws:s3:::entropy-jobs-${ACCOUNT_ID}/*\"
      },
      {
        \"Effect\": \"Allow\",
        \"Action\": [\"s3:ListBucket\"],
        \"Resource\": \"arn:aws:s3:::entropy-jobs-${ACCOUNT_ID}\"
      },
      {
        \"Effect\": \"Allow\",
        \"Action\": [\"sqs:SendMessage\", \"sqs:ReceiveMessage\", \"sqs:DeleteMessage\", \"sqs:GetQueueAttributes\"],
        \"Resource\": \"arn:aws:sqs:us-east-1:${ACCOUNT_ID}:entropy-jobs\"
      },
      {
        \"Effect\": \"Allow\",
        \"Action\": \"secretsmanager:GetSecretValue\",
        \"Resource\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/*\"
      }
    ]
  }"
```

- [ ] **Step 4: Create GitHub OIDC provider (if not already present)**

```bash
# Check if OIDC provider already exists
aws iam list-open-id-connect-providers \
  --query 'OpenIDConnectProviderList[].Arn' --output text | grep token.actions.githubusercontent.com

# If not found, create it:
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

- [ ] **Step 5: Create GitHub Actions IAM role**

```bash
aws iam create-role \
  --role-name entropy-github-actions-role \
  --assume-role-policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Effect\": \"Allow\",
      \"Principal\": {\"Federated\": \"arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com\"},
      \"Action\": \"sts:AssumeRoleWithWebIdentity\",
      \"Condition\": {
        \"StringEquals\": {
          \"token.actions.githubusercontent.com:aud\": \"sts.amazonaws.com\"
        },
        \"StringLike\": {
          \"token.actions.githubusercontent.com:sub\": \"repo:dp-pcs/entropy-builder:*\"
        }
      }
    }]
  }"

aws iam put-role-policy \
  --role-name entropy-github-actions-role \
  --policy-name entropy-github-actions-policy \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"ecr:GetAuthorizationToken\",
          \"ecr:BatchGetImage\",
          \"ecr:GetDownloadUrlForLayer\",
          \"ecr:BatchCheckLayerAvailability\",
          \"ecr:PutImage\",
          \"ecr:InitiateLayerUpload\",
          \"ecr:UploadLayerPart\",
          \"ecr:CompleteLayerUpload\"
        ],
        \"Resource\": \"*\"
      },
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"ecs:UpdateService\",
          \"ecs:DescribeServices\",
          \"ecs:RegisterTaskDefinition\",
          \"ecs:DescribeTaskDefinition\",
          \"iam:PassRole\"
        ],
        \"Resource\": \"*\"
      }
    ]
  }"

GITHUB_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/entropy-github-actions-role"
echo "GitHub Actions Role ARN: $GITHUB_ROLE_ARN"
```

- [ ] **Step 6: Add AWS_ROLE_ARN to GitHub repository secrets**

Go to: `https://github.com/dp-pcs/entropy-builder/settings/secrets/actions`

Add secret:
- Name: `AWS_ROLE_ARN`
- Value: the ARN printed above (`arn:aws:iam::{ACCOUNT_ID}:role/entropy-github-actions-role`)

---

## Task 7: ECS cluster + ALB + target group

**Resources:**
- ECS cluster: `entropy-cluster`
- ALB: `entropy-alb`
- Target group: `entropy-web-tg`

- [ ] **Step 1: Create ECS cluster**

```bash
aws ecs create-cluster \
  --cluster-name entropy-cluster \
  --region us-east-1
```

Expected: cluster status ACTIVE.

- [ ] **Step 2: Create ALB**

```bash
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name entropy-alb \
  --subnets "$SUBNET_1A" "$SUBNET_1B" \
  --security-groups "$ALB_SG" \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --region us-east-1 \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns "$ALB_ARN" \
  --query 'LoadBalancers[0].DNSName' --output text)

echo "ALB ARN: $ALB_ARN"
echo "ALB DNS: $ALB_DNS"
```

- [ ] **Step 3: Create target group**

```bash
TG_ARN=$(aws elbv2 create-target-group \
  --name entropy-web-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id "$VPC_ID" \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region us-east-1 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

echo "Target group: $TG_ARN"
```

- [ ] **Step 4: Create HTTPS listener with ACM cert**

```bash
aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn="$CERT_ARN" \
  --default-actions Type=forward,TargetGroupArn="$TG_ARN" \
  --region us-east-1

# HTTP → HTTPS redirect
aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTP \
  --port 80 \
  --default-actions \
    "Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
  --region us-east-1
```

- [ ] **Step 5: Add Route 53 A record for entropy.elelem.expert**

```bash
ALB_HOSTED_ZONE=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns "$ALB_ARN" \
  --query 'LoadBalancers[0].CanonicalHostedZoneId' --output text)

aws route53 change-resource-record-sets \
  --hosted-zone-id "$ZONE_ID" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"CREATE\",
      \"ResourceRecordSet\": {
        \"Name\": \"entropy.elelem.expert\",
        \"Type\": \"A\",
        \"AliasTarget\": {
          \"HostedZoneId\": \"${ALB_HOSTED_ZONE}\",
          \"DNSName\": \"${ALB_DNS}\",
          \"EvaluateTargetHealth\": false
        }
      }
    }]
  }"
```

---

## Task 8: ECS task definitions + web service

**Resources:**
- CloudWatch log group: `/ecs/entropy`
- ECS task definition: `entropy-web`
- ECS service: `entropy-web-service`

- [ ] **Step 1: Get resource values needed for task definition**

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="entropy-jobs-${ACCOUNT_ID}"
QUEUE_URL=$(aws sqs get-queue-url --queue-name entropy-jobs --query QueueUrl --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/entropy-builder"
TASK_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/entropy-task-execution-role"

echo "QUEUE_URL: $QUEUE_URL"
echo "ECR_URI: $ECR_URI"
```

- [ ] **Step 2: Create CloudWatch log group**

```bash
aws logs create-log-group --log-group-name /ecs/entropy --region us-east-1
```

- [ ] **Step 3: Register web task definition**

```bash
aws ecs register-task-definition \
  --family entropy-web \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 512 \
  --memory 1024 \
  --execution-role-arn "$TASK_ROLE_ARN" \
  --task-role-arn "$TASK_ROLE_ARN" \
  --container-definitions "[{
    \"name\": \"entropy-web\",
    \"image\": \"${ECR_URI}:latest\",
    \"portMappings\": [{\"containerPort\": 8000, \"protocol\": \"tcp\"}],
    \"command\": [\"uvicorn\", \"webapp.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"],
    \"environment\": [
      {\"name\": \"S3_BUCKET\", \"value\": \"${BUCKET}\"},
      {\"name\": \"AWS_REGION\", \"value\": \"us-east-1\"},
      {\"name\": \"SQS_QUEUE_URL\", \"value\": \"${QUEUE_URL}\"},
      {\"name\": \"BASE_URL\", \"value\": \"https://entropy.elelem.expert\"},
      {\"name\": \"NOTION_DATABASE_ID\", \"value\": \"28485e927d3181c89d6cdd6fd57ea07d\"},
      {\"name\": \"ENTROPY_TEMPLATE_PATH\", \"value\": \"/app/entropy-template\"}
    ],
    \"secrets\": [
      {\"name\": \"NOTION_TOKEN\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/NOTION_TOKEN\"},
      {\"name\": \"FIREWORKS_API_KEY\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/FIREWORKS_API_KEY\"},
      {\"name\": \"GOOGLE_CLIENT_ID\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/GOOGLE_CLIENT_ID\"},
      {\"name\": \"GOOGLE_CLIENT_SECRET\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/GOOGLE_CLIENT_SECRET\"}
    ],
    \"logConfiguration\": {
      \"logDriver\": \"awslogs\",
      \"options\": {
        \"awslogs-group\": \"/ecs/entropy\",
        \"awslogs-region\": \"us-east-1\",
        \"awslogs-stream-prefix\": \"web\"
      }
    },
    \"healthCheck\": {
      \"command\": [\"CMD-SHELL\", \"curl -f http://localhost:8000/health || exit 1\"],
      \"interval\": 30,
      \"timeout\": 5,
      \"retries\": 3
    }
  }]"
```

- [ ] **Step 4: Create web ECS service**

```bash
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=entropy-vpc" \
  --query 'Vpcs[0].VpcId' --output text)
SUBNET_1A=$(aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=entropy-public-1a" \
  --query 'Subnets[0].SubnetId' --output text)
SUBNET_1B=$(aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=entropy-public-1b" \
  --query 'Subnets[0].SubnetId' --output text)
WEB_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=entropy-web-sg" "Name=vpc-id,Values=$VPC_ID" \
  --query 'SecurityGroups[0].GroupId' --output text)
TG_ARN=$(aws elbv2 describe-target-groups \
  --names entropy-web-tg \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

aws ecs create-service \
  --cluster entropy-cluster \
  --service-name entropy-web-service \
  --task-definition entropy-web \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[\"$SUBNET_1A\",\"$SUBNET_1B\"],
    securityGroups=[\"$WEB_SG\"],
    assignPublicIp=ENABLED
  }" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=entropy-web,containerPort=8000" \
  --region us-east-1
```

- [ ] **Step 5: Verify service is running**

```bash
aws ecs describe-services \
  --cluster entropy-cluster \
  --services entropy-web-service \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

Expected: `{"Status": "ACTIVE", "Running": 1, "Desired": 1}`

---

## Task 9: ECS worker service

**Resources:**
- ECS task definition: `entropy-worker`
- ECS service: `entropy-worker-service`
- Application Auto Scaling policy (scale on SQS queue depth)

- [ ] **Step 1: Register worker task definition**

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="entropy-jobs-${ACCOUNT_ID}"
QUEUE_URL=$(aws sqs get-queue-url --queue-name entropy-jobs --query QueueUrl --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/entropy-builder"
TASK_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/entropy-task-execution-role"

aws ecs register-task-definition \
  --family entropy-worker \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 2048 \
  --memory 8192 \
  --execution-role-arn "$TASK_ROLE_ARN" \
  --task-role-arn "$TASK_ROLE_ARN" \
  --container-definitions "[{
    \"name\": \"entropy-worker\",
    \"image\": \"${ECR_URI}:latest\",
    \"command\": [\"python\", \"-m\", \"worker\"],
    \"environment\": [
      {\"name\": \"S3_BUCKET\", \"value\": \"${BUCKET}\"},
      {\"name\": \"AWS_REGION\", \"value\": \"us-east-1\"},
      {\"name\": \"SQS_QUEUE_URL\", \"value\": \"${QUEUE_URL}\"},
      {\"name\": \"NOTION_DATABASE_ID\", \"value\": \"28485e927d3181c89d6cdd6fd57ea07d\"},
      {\"name\": \"ENTROPY_TEMPLATE_PATH\", \"value\": \"/app/entropy-template\"}
    ],
    \"secrets\": [
      {\"name\": \"NOTION_TOKEN\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/NOTION_TOKEN\"},
      {\"name\": \"FIREWORKS_API_KEY\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/FIREWORKS_API_KEY\"},
      {\"name\": \"GOOGLE_CLIENT_ID\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/GOOGLE_CLIENT_ID\"},
      {\"name\": \"GOOGLE_CLIENT_SECRET\", \"valueFrom\": \"arn:aws:secretsmanager:us-east-1:${ACCOUNT_ID}:secret:entropy/GOOGLE_CLIENT_SECRET\"}
    ],
    \"logConfiguration\": {
      \"logDriver\": \"awslogs\",
      \"options\": {
        \"awslogs-group\": \"/ecs/entropy\",
        \"awslogs-region\": \"us-east-1\",
        \"awslogs-stream-prefix\": \"worker\"
      }
    }
  }]"
```

- [ ] **Step 2: Create worker ECS service**

```bash
WORKER_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=entropy-worker-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)
SUBNET_1A=$(aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=entropy-public-1a" \
  --query 'Subnets[0].SubnetId' --output text)
SUBNET_1B=$(aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=entropy-public-1b" \
  --query 'Subnets[0].SubnetId' --output text)

aws ecs create-service \
  --cluster entropy-cluster \
  --service-name entropy-worker-service \
  --task-definition entropy-worker \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[\"$SUBNET_1A\",\"$SUBNET_1B\"],
    securityGroups=[\"$WORKER_SG\"],
    assignPublicIp=ENABLED
  }" \
  --region us-east-1
```

- [ ] **Step 3: Register Application Auto Scaling for worker**

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/entropy-cluster/entropy-worker-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 5

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/entropy-cluster/entropy-worker-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name entropy-worker-scale-on-queue \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration "{
    \"CustomizedMetricSpecification\": {
      \"MetricName\": \"ApproximateNumberOfMessagesVisible\",
      \"Namespace\": \"AWS/SQS\",
      \"Dimensions\": [{\"Name\": \"QueueName\", \"Value\": \"entropy-jobs\"}],
      \"Statistic\": \"Maximum\"
    },
    \"TargetValue\": 1,
    \"ScaleInCooldown\": 300,
    \"ScaleOutCooldown\": 60
  }"
```

- [ ] **Step 4: Verify worker service is running**

```bash
aws ecs describe-services \
  --cluster entropy-cluster \
  --services entropy-worker-service \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

Expected: `{"Status": "ACTIVE", "Running": 1, "Desired": 1}`

---

## Task 10: GitHub Actions deploy workflow

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create the workflow file**

```bash
mkdir -p .github/workflows
```

```yaml
# .github/workflows/deploy.yml
name: Deploy to ECS

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Log in to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/entropy-builder:$IMAGE_TAG .
          docker push $ECR_REGISTRY/entropy-builder:$IMAGE_TAG
          docker tag $ECR_REGISTRY/entropy-builder:$IMAGE_TAG $ECR_REGISTRY/entropy-builder:latest
          docker push $ECR_REGISTRY/entropy-builder:latest

      - name: Update ECS web service
        run: |
          aws ecs update-service \
            --cluster entropy-cluster \
            --service entropy-web-service \
            --force-new-deployment \
            --region us-east-1

      - name: Update ECS worker service
        run: |
          aws ecs update-service \
            --cluster entropy-cluster \
            --service entropy-worker-service \
            --force-new-deployment \
            --region us-east-1

      - name: Wait for web service to stabilize
        run: |
          aws ecs wait services-stable \
            --cluster entropy-cluster \
            --services entropy-web-service \
            --region us-east-1
          echo "Deployment complete"
```

- [ ] **Step 2: Push first image manually to unblock ECS service startup**

ECS services were created with `entropy-builder:latest` but the image doesn't exist yet. Push it now:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/entropy-builder"

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"

docker build -t "$ECR_URI:latest" .
docker push "$ECR_URI:latest"
```

- [ ] **Step 3: Force ECS services to pick up the new image**

```bash
aws ecs update-service \
  --cluster entropy-cluster \
  --service entropy-web-service \
  --force-new-deployment

aws ecs update-service \
  --cluster entropy-cluster \
  --service entropy-worker-service \
  --force-new-deployment
```

- [ ] **Step 4: Commit and push the workflow**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: add GitHub Actions ECS deploy workflow via OIDC"
git push
```

- [ ] **Step 5: Verify GitHub Actions runs successfully**

Go to `https://github.com/dp-pcs/entropy-builder/actions`. The deploy workflow should run on the push and complete with a green checkmark.

---

## Task 11: Smoke test end-to-end

- [ ] **Step 1: Verify HTTPS is live**

```bash
curl -I https://entropy.elelem.expert/health
```

Expected: `HTTP/2 200` with body `{"status":"ok"}`

- [ ] **Step 2: Verify wizard loads**

```bash
curl -s https://entropy.elelem.expert/wizard | grep -o "<title>.*</title>"
```

Expected: title containing "Entropy"

- [ ] **Step 3: Verify account managers API**

```bash
curl -s https://entropy.elelem.expert/api/notion/account-managers
```

Expected: `{"managers": [...]}` — list of account manager names from Notion.

- [ ] **Step 4: Verify Google OAuth redirect**

Open `https://entropy.elelem.expert/oauth/google?session_id=00000000-0000-0000-0000-000000000001` in a browser. Should redirect to Google's OAuth consent screen.

- [ ] **Step 5: Check ECS logs for any errors**

```bash
aws logs tail /ecs/entropy --follow --filter-pattern "ERROR"
```

Expected: no errors during idle operation.

---

## Self-Review

### 1. Spec coverage

| Spec requirement | Task covering it |
|---|---|
| S3 bucket with AES256 + lifecycle rules | Task 1 |
| Secrets Manager (4 secrets) | Task 2 |
| SQS queue + DLQ (3-hour visibility) | Task 3 |
| VPC + 2 public subnets + IGW | Task 4 |
| Security groups (ALB, web, worker) | Task 4 |
| ACM cert for entropy.elelem.expert | Task 5 |
| Route 53 CNAME validation + A record | Task 5 + Task 7 |
| ECR repository | Task 6 |
| IAM task execution role (S3+SQS+Secrets) | Task 6 |
| GitHub OIDC role for entropy-builder repo | Task 6 |
| ECS cluster | Task 7 |
| ALB + target group + HTTPS listener | Task 7 |
| HTTP → HTTPS redirect | Task 7 |
| ECS web task definition + service | Task 8 |
| ECS worker task definition + service | Task 9 |
| Auto-scaling on SQS queue depth | Task 9 |
| GitHub Actions deploy workflow | Task 10 |
| First manual image push + smoke test | Tasks 10–11 |

### 2. Placeholder scan

- Task 2 Step 1: `YOUR_NOTION_TOKEN` etc. — intentional; engineer replaces with real values from `.env`. Not a spec placeholder.

### 3. Consistency

- `ACCOUNT_ID` variable re-derived at start of Tasks 8 and 9 using `aws sts get-caller-identity` — consistent with pattern established in Task 1.
- ECR image URI format `${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/entropy-builder` consistent across Tasks 6, 8, 9, 10.
- `entropy-task-execution-role` used as both `executionRoleArn` and `taskRoleArn` in task definitions — consistent and correct (the role has permissions for both ECS plumbing and app-level S3/SQS/Secrets access).

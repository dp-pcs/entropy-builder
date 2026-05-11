import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    s3_bucket: str = field(default_factory=lambda: os.environ.get("S3_BUCKET", ""))
    aws_region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    google_client_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_ID", ""))
    google_client_secret: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_SECRET", ""))
    notion_client_id: str = field(default_factory=lambda: os.environ.get("NOTION_CLIENT_ID", ""))
    notion_client_secret: str = field(default_factory=lambda: os.environ.get("NOTION_CLIENT_SECRET", ""))
    notion_database_id: str = field(default_factory=lambda: os.environ.get("NOTION_DATABASE_ID", "28485e927d3181c89d6cdd6fd57ea07d"))
    fireworks_api_key: str = field(default_factory=lambda: os.environ.get("FIREWORKS_API_KEY", ""))
    entropy_template_path: str = field(default_factory=lambda: os.environ.get("ENTROPY_TEMPLATE_PATH", ""))
    base_url: str = field(default_factory=lambda: os.environ.get("BASE_URL", "http://localhost:8000"))

settings = Settings()

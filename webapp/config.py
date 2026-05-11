import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    s3_bucket: str = field(default_factory=lambda: os.environ.get("S3_BUCKET", ""))
    aws_region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    sqs_queue_url: str = field(default_factory=lambda: os.environ.get("SQS_QUEUE_URL", ""))
    google_client_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_ID", ""))
    google_client_secret: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_SECRET", ""))
    notion_database_id: str = field(default_factory=lambda: os.environ.get("NOTION_DATABASE_ID", "3bb5b1a03a5782d8aaf781dc88e58df7"))
    notion_token: str = field(default_factory=lambda: os.environ.get("NOTION_TOKEN", ""))
    fireworks_api_key: str = field(default_factory=lambda: os.environ.get("FIREWORKS_API_KEY", ""))
    entropy_template_path: str = field(default_factory=lambda: os.environ.get("ENTROPY_TEMPLATE_PATH", ""))
    base_url: str = field(default_factory=lambda: os.environ.get("BASE_URL", "http://localhost:8000"))
    notion_mcp_package: str = field(default_factory=lambda: os.environ.get("NOTION_MCP_PACKAGE", "@notionhq/notion-mcp-server"))
    gmail_mcp_package: str = field(default_factory=lambda: os.environ.get("GMAIL_MCP_PACKAGE", "@modelcontextprotocol/server-gmail"))
    readai_mcp_package: str = field(default_factory=lambda: os.environ.get("READAI_MCP_PACKAGE", "@read-ai/mcp-server"))

settings = Settings()

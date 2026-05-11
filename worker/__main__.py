import json
import logging
import sys

import boto3

from webapp import s3
from webapp.config import settings
from webapp.jobs import run_pipeline_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _process_message(sqs_client, queue_url: str, msg: dict) -> None:
    receipt = msg["ReceiptHandle"]
    try:
        body = json.loads(msg["Body"])
        job_id = body["job_id"]
    except (json.JSONDecodeError, KeyError):
        logger.warning("Unparseable message body — deleting: %s", msg.get("Body", "")[:200])
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
        return

    s3_keys = body.get("s3_keys", [])

    config = s3.read_job_config(job_id)
    if config is None:
        logger.warning("No config found for job %s — deleting message", job_id)
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
        return

    try:
        run_pipeline_job(job_id, config, s3_keys)
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
        logger.info("Job %s completed", job_id)
    except Exception:
        logger.exception("Job %s failed — leaving message for SQS retry", job_id)
        # Do NOT delete — SQS retries up to 3x, then routes to DLQ


def main() -> None:
    queue_url = settings.sqs_queue_url
    if not queue_url:
        logger.error("SQS_QUEUE_URL not set — exiting")
        sys.exit(1)

    sqs = boto3.client("sqs", region_name=settings.aws_region)
    logger.info("Worker started, polling %s", queue_url)

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            WaitTimeSeconds=20,
            MaxNumberOfMessages=1,
        )
        for msg in response.get("Messages", []):
            _process_message(sqs, queue_url, msg)


if __name__ == "__main__":
    main()

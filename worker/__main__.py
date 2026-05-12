import json
import logging
import signal
import sys
import threading

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

# Set by signal handler; checked in the poll loop.
_shutdown = threading.Event()

# Receipt handle of the message currently being processed (if any).
_current_receipt: str | None = None
_current_receipt_lock = threading.Lock()
_sqs_client_ref: "boto3.client | None" = None
_queue_url_ref: str = ""


def _handle_sigterm(signum, frame) -> None:
    logger.info("SIGTERM received — finishing current job then exiting")
    _shutdown.set()
    # Release the in-flight SQS message immediately so another worker can retry it
    # without waiting for the 3-hour visibility timeout.
    with _current_receipt_lock:
        receipt = _current_receipt
    if receipt and _sqs_client_ref:
        try:
            _sqs_client_ref.change_message_visibility(
                QueueUrl=_queue_url_ref,
                ReceiptHandle=receipt,
                VisibilityTimeout=0,
            )
            logger.info("Released in-flight SQS message for immediate retry")
        except Exception as exc:
            logger.warning("Could not release SQS message: %s", exc)


def _process_message(sqs_client, queue_url: str, msg: dict) -> None:
    global _current_receipt
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

    with _current_receipt_lock:
        _current_receipt = receipt
    try:
        run_pipeline_job(job_id, config, s3_keys)
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
        logger.info("Job %s completed", job_id)
    except Exception:
        logger.exception("Job %s failed — leaving message for SQS retry", job_id)
        # Do NOT delete — SQS retries up to 3x, then routes to DLQ
    finally:
        with _current_receipt_lock:
            _current_receipt = None


def main() -> None:
    global _sqs_client_ref, _queue_url_ref

    queue_url = settings.sqs_queue_url
    if not queue_url:
        logger.error("SQS_QUEUE_URL not set — exiting")
        sys.exit(1)

    sqs = boto3.client("sqs", region_name=settings.aws_region)
    _sqs_client_ref = sqs
    _queue_url_ref = queue_url

    signal.signal(signal.SIGTERM, _handle_sigterm)

    logger.info("Worker started, polling %s", queue_url)

    while not _shutdown.is_set():
        response = sqs.receive_message(
            QueueUrl=queue_url,
            WaitTimeSeconds=20,
            MaxNumberOfMessages=1,
        )
        for msg in response.get("Messages", []):
            _process_message(sqs, queue_url, msg)

    logger.info("Worker shut down cleanly")


if __name__ == "__main__":
    main()

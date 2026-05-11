# tests/worker/test_worker.py
import json
from unittest.mock import MagicMock


def _make_msg(job_id: str = "job-123", s3_keys: list = None, receipt: str = "rcpt-abc") -> dict:
    return {
        "Body": json.dumps({"job_id": job_id, "s3_keys": s3_keys or []}),
        "ReceiptHandle": receipt,
    }


def test_process_message_success(mocker):
    from worker.__main__ import _process_message

    config = {"user_name": "Alice", "notion_token": "n-tok"}
    mocker.patch("worker.__main__.s3.read_job_config", return_value=config)
    mock_run = mocker.patch("worker.__main__.run_pipeline_job")

    sqs_client = MagicMock()
    queue_url = "https://sqs.us-east-1.amazonaws.com/123/test-queue"
    msg = _make_msg(job_id="job-123", s3_keys=["jobs/job-123/upload.zip"], receipt="rcpt-abc")

    _process_message(sqs_client, queue_url, msg)

    mock_run.assert_called_once_with("job-123", config, ["jobs/job-123/upload.zip"])
    sqs_client.delete_message.assert_called_once_with(
        QueueUrl=queue_url, ReceiptHandle="rcpt-abc"
    )


def test_process_message_missing_config(mocker):
    from worker.__main__ import _process_message

    mocker.patch("worker.__main__.s3.read_job_config", return_value=None)
    mock_run = mocker.patch("worker.__main__.run_pipeline_job")

    sqs_client = MagicMock()
    queue_url = "https://sqs.us-east-1.amazonaws.com/123/test-queue"
    msg = _make_msg(job_id="job-missing", receipt="rcpt-no-config")

    _process_message(sqs_client, queue_url, msg)

    sqs_client.delete_message.assert_called_once_with(
        QueueUrl=queue_url, ReceiptHandle="rcpt-no-config"
    )
    mock_run.assert_not_called()


def test_process_message_invalid_body(mocker):
    from worker.__main__ import _process_message

    mock_run = mocker.patch("worker.__main__.run_pipeline_job")

    sqs_client = MagicMock()
    queue_url = "https://sqs.us-east-1.amazonaws.com/123/test-queue"
    msg = {"Body": "not valid json", "ReceiptHandle": "rcpt-bad"}

    _process_message(sqs_client, queue_url, msg)

    sqs_client.delete_message.assert_called_once_with(
        QueueUrl=queue_url, ReceiptHandle="rcpt-bad"
    )
    mock_run.assert_not_called()


def test_process_message_pipeline_failure(mocker):
    from worker.__main__ import _process_message

    config = {"user_name": "Bob", "notion_token": "n-tok"}
    mocker.patch("worker.__main__.s3.read_job_config", return_value=config)
    mocker.patch("worker.__main__.run_pipeline_job", side_effect=RuntimeError("pipeline exploded"))

    sqs_client = MagicMock()
    queue_url = "https://sqs.us-east-1.amazonaws.com/123/test-queue"
    msg = _make_msg(job_id="job-fail", receipt="rcpt-fail")

    _process_message(sqs_client, queue_url, msg)

    sqs_client.delete_message.assert_not_called()

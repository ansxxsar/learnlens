import logging

from celery import shared_task

from .services import execute_submission

logger = logging.getLogger(__name__)


# acks_late: if the worker dies mid-run, the broker hands the job out again.
@shared_task(acks_late=True, ignore_result=True)
def run_submission(submission_id):
    execute_submission(submission_id)


def enqueue_submission(submission_id):
    """Sends an attempt to the workers. A broker outage must not lose the
    attempt or fail the student's request: it stays queued and can be sent
    again with manage.py requeue_submissions."""
    try:
        run_submission.delay(submission_id)
    except Exception:
        logger.exception('could not queue submission %s', submission_id)

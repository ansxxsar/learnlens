from django.core.management.base import BaseCommand

from execution.tasks import enqueue_submission
from submissions.models import Submission

Status = Submission.Status


class Command(BaseCommand):
    help = (
        'Sends queued attempts to the workers again, for example after Redis was down. '
        'Use --failed to retry attempts the runner could not run.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--failed', action='store_true', help='also retry failed attempts')
        parser.add_argument(
            '--running',
            action='store_true',
            help='also retry attempts stuck in running (only when no worker is running)',
        )

    def handle(self, *args, failed, running, **options):
        statuses = [Status.QUEUED]
        if failed:
            statuses.append(Status.FAILED)
        if running:
            statuses.append(Status.RUNNING)

        ids = list(Submission.objects.filter(status__in=statuses).values_list('id', flat=True))
        Submission.objects.filter(id__in=ids).update(status=Status.QUEUED)
        for submission_id in ids:
            enqueue_submission(submission_id)
        self.stdout.write(f'Queued {len(ids)} attempt(s).')

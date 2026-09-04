
from celery import shared_task
from .models import Pitch
from .services import PitchGenerationError, generate_pitch
from common import handle_error_log

APP_NAME = 'campaigns'


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # seconds — backs off on transient Claude/network errors
)
def generate_pitch_task(self, pitch_id: str) -> None:
    try:
        pitch = Pitch.objects.select_related("campaign", "contact").get(pk=pitch_id)
    except Pitch.DoesNotExist:
        handle_error_log(e=f"generate_pitch_task: Pitch %s no longer exists, skipping. {pitch_id}", view_name= 'tasks.generate_pitch_task', app_name=APP_NAME)
        return

    try:
        result = generate_pitch(pitch.campaign, pitch.contact)
        pitch.mark_ready(subject=result["subject"], body=result["body"])

    except PitchGenerationError as exc:
        pitch.mark_failed(str(exc))
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            handle_error_log(e=f"generate_pitch_task: giving up on pitch %s after retries. {pitch_id}", view_name= 'tasks.generate_pitch_task', app_name=APP_NAME)

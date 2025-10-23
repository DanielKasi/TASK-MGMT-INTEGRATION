from .models import ProjectTaskEmailConfig
from .task import send_project_or_task_email
from django.conf import settings

def send_email_for_task_status_change(task):
    """
    Send email notifications based on task status changes (completion/failure).
    Called after task status is updated.
    """
    is_completed = False
    is_failed = False
    task_email_config = None

    # Determine intent and fetch config safely
    if task.applied_project_task_status == task.project.completed_status:
        is_completed = True
        try:
            task_email_config = ProjectTaskEmailConfig.objects.get(
                intent=ProjectTaskEmailConfig.Intent.COMPLETION,
                project=task.project,
                is_active=True,
                deleted_at__isnull=True,
            )
        except ProjectTaskEmailConfig.DoesNotExist:
            return  

    elif task.applied_project_task_status == task.project.failed_status:
        is_failed = True
        try:
            task_email_config = ProjectTaskEmailConfig.objects.get(
                intent=ProjectTaskEmailConfig.Intent.FAILURE,
                project=task.project,
                is_active=True,
                deleted_at__isnull=True,
            )
        except ProjectTaskEmailConfig.DoesNotExist:
            return

    if not (is_completed or is_failed) or task_email_config is None:
        return

    # Get recipient IDs
    task_manager_id = task.user_manager.id if task.user_manager else None
    task_issuer_id = task.created_by.id if task.created_by else None
    task_assignee_ids = list(task.user_assignees.values_list('user_assigned_id', flat=True))

    _send_configured_emails(
        task_manager_id=task_manager_id,
        task_issuer_id=task_issuer_id,
        task_assignee_ids=task_assignee_ids,
        task=task,
        is_completed=is_completed,
        is_failed=is_failed,
        config=task_email_config
    )


def _send_configured_emails(task_manager_id, task_issuer_id, task_assignee_ids, task, is_completed, is_failed, config):
    """Send emails based on project email configuration."""
    frontend_url = settings.FRONTEND_URL
    task_url = f"{frontend_url}/task-mgt/task/{task.id}"
    
    manager_ids = []
    assignee_ids = []
    
    if config.task_issuer and task_issuer_id:
        manager_ids.append(task_issuer_id)
    if config.task_leader and task_manager_id:
        manager_ids.append(task_manager_id)
    if config.task_assignees and task_assignee_ids:
        assignee_ids.extend(task_assignee_ids)
    
    manager_ids = list(set(manager_ids))
    assignee_ids = list(set(assignee_ids))
    
    if manager_ids or assignee_ids:
        send_project_or_task_email.delay_on_commit(
            user_manager_ids=manager_ids,
            user_assignee_ids=assignee_ids,
            url=task_url,
            task_id=task.id,
            is_completed=is_completed,
            is_failed=is_failed,
        )
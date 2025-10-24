from .models import StandaloneTaskEmailConfig
from .task import send_project_or_task_email
from django.conf import settings

def send_email_for_task_status_change(task):
    """
    Send email notifications for standalone task status changes (completion/failure),
    based on StandaloneTaskEmailConfig.
    Called after task status is updated.
    """
    print(f"Entering the email sending function for standalone task: {task.id}")
    
    is_completed = False
    is_failed = False
    intent = None

    if task.applied_task_status == task.completed_status:
        intent = StandaloneTaskEmailConfig.Intent.COMPLETION
        is_completed = True
    elif task.applied_task_status == task.failed_status:
        intent = StandaloneTaskEmailConfig.Intent.FAILURE
        is_failed = True
    else:
        return  
    
    try:
        config = StandaloneTaskEmailConfig.objects.get(
            task=task,
            intent=intent,
            is_active=True,
            deleted_at__isnull=True,
        )
    except StandaloneTaskEmailConfig.DoesNotExist:
        print(f"No email config found for standalone task {task.id} and intent {intent}")
        return  

    task_manager_id = task.user_manager.id if task.user_manager else None
    task_issuer_id = task.created_by.id if task.created_by else None
    task_assignee_ids = list(task.user_assignees.values_list('user_assigned_id', flat=True))

    _send_standalone_task_emails(
        task_manager_id=task_manager_id,
        task_issuer_id=task_issuer_id,
        task_assignee_ids=task_assignee_ids,
        task=task,
        is_completed=is_completed,
        is_failed=is_failed,
        config=config
    )


def _send_standalone_task_emails(task_manager_id, task_issuer_id, task_assignee_ids, task, is_completed, is_failed, config):
    """Send emails respecting StandaloneTaskEmailConfig."""
    frontend_url = settings.FRONTEND_URL
    task_url = f"{frontend_url}/task-mgt/task/{task.id}"
    
    manager_ids = []
    assignee_ids = []

    # Apply config flags
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
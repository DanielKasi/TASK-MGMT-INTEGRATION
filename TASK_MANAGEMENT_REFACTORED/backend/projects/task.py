from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from projects.models import Task, Project
from users.models import CustomUser
from utilities.helpers import get_personalized_greeting
from celery import shared_task

# Helper function
def _send_to_group(users, subject, url, role_label, project=None, task=None, template=None):
    for user in users:
        print(f"Sending email to: {user.email}")
        if project is not None:
            company_name = project.institution.institution_name if hasattr(project, 'institution') and project.institution else "Your Company"
        elif task is not None:
            company = task.get_institution() if hasattr(task, 'get_institution') else "Your Company"
            company_name = company.institution_name
        else:
            company_name = "Your Company"

        task_project_name = None
        if task is not None and hasattr(task, 'project') and task.project is not None:
            task_project_name = task.project.project_name if hasattr(task.project, 'project_name') else task.project.name

        salutation = "Mr"
        if user.gender is not None:
            if user.gender == "male":
                salutation = "Mr"
            elif user.gender == "female":
                salutation = "Ms"
        
        context = {
            "role_label": role_label,
            "user": user,
            "project": project,
            "salutation": salutation,
            "task": task,
            "url": url,
            "company_name": company_name,
            "task_project_name": task_project_name,
            "fullname": user.fullname,
            "year": timezone.now().year,
            "personalized_greeting": get_personalized_greeting(user),
        }
        
        html_message = render_to_string(template, context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )

        print(f"Completed sending email to: {user.email}")

@shared_task
def send_project_or_task_email(
    user_manager_ids,
    user_assignee_ids,
    url,
    project_id=None,
    task_id=None,
    is_update=False,
    is_completed=False,   
    is_failed=False,      
):

    # Fetch users
    managers = CustomUser.objects.filter(id__in=user_manager_ids)
    assignees = CustomUser.objects.filter(id__in=user_assignee_ids)

    assignee_role = "Assignee"
    manager_role = "Manager"

    if project_id is not None:
        # Projects only support creation/update (no success/failure)
        project = Project.objects.get(id=project_id)
        subject = "Project Updated" if is_update else "New Project Assignment"
        template = (
            "emails/projects/projects_update_email.html"
            if is_update
            else "emails/projects/projects_creation_email.html"
        )
        _send_to_group(managers, subject, url, role_label=manager_role, project=project, template=template)
        _send_to_group(assignees, subject, url, role_label=assignee_role, project=project, template=template)

    elif task_id is not None:
        task = Task.objects.get(id=task_id)

        # Determine email type based on boolean flags
        if is_completed:
            subject = "Task Completed Successfully"
            template = "emails/tasks/tasks_completion_email.html"
        elif is_failed:
            subject = "Task Failed Action Required"
            template = "emails/tasks/tasks_failure_email.html"
        elif is_update:
            subject = "Task Updated"
            template = "emails/tasks/tasks_update_email.html"
        else:
            # Default: new task assignment
            subject = "New Task Assignment"
            template = "emails/tasks/tasks_creation_email.html"

        # Send to both managers and assignees
        _send_to_group(managers, subject, url, role_label=manager_role, task=task, template=template)
        _send_to_group(assignees, subject, url, role_label=assignee_role, task=task, template=template)

    return True

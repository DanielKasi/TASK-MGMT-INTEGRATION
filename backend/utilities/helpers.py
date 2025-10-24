from urllib.parse import urlparse
from django.utils import timezone
from django.http import HttpResponseForbidden
from functools import wraps
import hashlib
from users.models import OneTimePassword
from django.conf import settings
import logging
import secrets
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from users.models import Role, RolePermission, Permission, UserRole


def custom_parse_date(value: str):
    if not value:
        return None

    value = value.strip().replace("“", "").replace("”", "")

    if " " in value:
        value = value.split()[0]

    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format. Use YYYY-MM-DD, YYYY/MM/DD, or YYYY.MM.DD")


def get_gender_salutation(user):
    """
    Returns appropriate salutation based on user's gender.

    Args:
        user: User object with gender field

    Returns:
        str: Appropriate salutation (Mr., Ms., or empty string)
    """
    if not hasattr(user, "gender") or not user.gender:
        return ""

    gender_salutations = {
        "male": "Mr.",
        "female": "Madam",
        "other": "",  # No salutation for 'other' or when gender is not specified
    }

    return gender_salutations.get(user.gender.lower(), "")


def get_personalized_greeting(user):
    """
    Returns a personalized greeting with salutation and name.

    Args:
        user: User object with gender and fullname fields

    Returns:
        str: Personalized greeting like "Mr. John Doe" or "Ms. Jane Smith"
    """
    salutation = get_gender_salutation(user)
    fullname = getattr(user, "fullname", "there")

    if salutation:
        return f"{salutation} {fullname}"
    return fullname


def get_or_create_default_role_with_permissions(institution):
    role, created = Role.objects.get_or_create(
        name="normal employee role",
        institution=institution,
        defaults={
            "description": "Default role for new employees",
        },
    )

    if created:
        default_permission_codes = [
            "can_view_employee_personal_data",
        ]

        default_permissions = Permission.objects.filter(
            permission_code__in=default_permission_codes
        )

        RolePermission.objects.bulk_create(
            [RolePermission(role=role, permission=perm) for perm in default_permissions]
        )

    return role


def send_activation_confirmation_email(
    owner_fullname,
    owner_email,
    institution_name,
    branches,
    departments,
    employees,
    owner_user=None,
):
    """
    Sends an email to the owner confirming the activation of the institution.
    """

    try:
        subject = "Perrac Module Activation Confirmation"

        # Get personalized greeting if user object is available
        if owner_user:
            personalized_name = get_personalized_greeting(owner_user)
        else:
            personalized_name = owner_fullname

        context = {
            "owner_full_name": personalized_name,
            "owner_email": owner_email,
            "institution_name": institution_name,
            "branches": len(branches),
            "departments": len(departments),
            "employees": len(employees),
            "year": timezone.now().year,
        }

        # Render HTML template
        html_message = render_to_string("activation-emails/perrac.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner_email],
            html_message=html_message,
        )
        logger.info(f"Activation confirmation email sent to {owner_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending activation confirmation email: {e}")
        raise e


def permission_required(perm_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.has_permission(
                perm_name
            ):
                return HttpResponseForbidden("Forbidden")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_required_any(perm_names):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")
            
            # Check if user has any of the required permissions
            if not any(request.user.has_permission(perm) for perm in perm_names):
                message = (
                    f"Access denied: You do not have the required permission '{perm_names}' "
                )
                return HttpResponseForbidden(message)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def generate_otp(length=6):
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(user_id, otp):
    raw_string = f"{user_id}-{otp}"
    return hashlib.sha256(raw_string.encode()).hexdigest()


def create_and_institution_otp(user_id, purpose=None, expiry_minutes=15):
    otp = generate_otp()
    otp_hash = hash_otp(user_id, otp)

    expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)

    if purpose:
        cleanup_existing_otps(user_id, purpose)

    OneTimePassword.objects.create(
        otp_hash=otp_hash, expiry=expiry_time, purpose=purpose
    )

    return otp


def cleanup_existing_otps(user_id, purpose):
    if purpose:
        OneTimePassword.objects.filter(purpose=purpose, is_used=False).delete()


def cleanup_expired_otps():
    """
    Utility function to clean up expired OTPs
    This can be called periodically via a scheduled task
    """
    now = timezone.now()
    deleted_count, _ = OneTimePassword.objects.filter(expiry__lt=now).delete()
    return deleted_count


def verify_otp(identifier, received_otp):
    otp_hash = hash_otp(identifier, received_otp)
    logger.debug(f"Verifying OTP hash: {otp_hash}")

    try:
        otp_entry = OneTimePassword.objects.get(otp_hash=otp_hash, is_used=False)

        if otp_entry.is_expired():
            logger.warning(f"OTP expired for hash: {otp_hash}")
            return False, "OTP has expired"

        otp_entry.delete()
        logger.info(f"OTP verified and deleted successfully for hash: {otp_hash}")
        return True, "OTP verified successfully"

    except OneTimePassword.DoesNotExist:
        logger.warning(f"Invalid OTP attempt with hash: {otp_hash}")
        return False, "Invalid OTP"


def send_plain_email(receivers, subject, body, fail_silently=False):
    """
    Send plain text email to list of receivers using Gmail SMTP

    Args:
        receivers: List of email addresses or single email address as string
        subject: Email subject
        body: Plain text email body
        fail_silently: If True, exceptions will be suppressed

    Returns:
        Number of successfully sent emails (0 or 1)
    """
    if isinstance(receivers, str):
        receivers = [receivers]

    try:
        num_sent = send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=receivers,
            fail_silently=fail_silently,
        )

        if num_sent > 0:
            logger.info(f"Email sent to {receivers} with subject: {subject}")
        else:
            logger.warning(f"Email failed to send to {receivers}")

        return num_sent

    except Exception as e:
        if not fail_silently:
            raise
        return 0


def send_otp_to_user(user, otp):
    subject = "Verify Your Account"

    context = {
        "user": user,
        "otp_code": otp,
        "year": timezone.now().year,
        "personalized_greeting": get_personalized_greeting(user),
    }

    # Render HTML template
    html_message = render_to_string(
        "users/emails/signup_otp_verification.html", context
    )
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )
    return True


def build_password_link(request, token: str) -> str:
    frontend_origin = request.headers.get("Origin")
    if frontend_origin:
        parts = urlparse(frontend_origin)
        base_link = f"{parts.scheme}://{parts.netloc}"
    else:
        base_link = f"{request.scheme}://{request.get_host()}"

    return f"{base_link.rstrip('/')}/reset-password/{token}"


def create_and_institution_token(user, purpose="registration", expiry_minutes=15):
    from users.models import OTPModel

    token = secrets.token_urlsafe(32)
    OTPModel.objects.create(
        user=user,
        value=token,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )
    return token


def send_password_link_to_user(user, link):
    subject = "Set Your Password"
    context = {
        "link": link,
        "user": user,
        "fullname": user.fullname,
        "year": timezone.now().year,
        "personalized_greeting": get_personalized_greeting(user),
    }
    html_message = render_to_string(
        "institutions/emails/signup_link_email.html", context
    )
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )
    return True


def send_password_reset_link_to_user(user, link):
    try:
        subject = "Reset Your Password"
        context = {
            "link": link,
            "user": user,
            "year": timezone.now().year,
            "personalized_greeting": get_personalized_greeting(user),
        }
        html_message = render_to_string("forgot-password/password-reset.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )
        return True
    except Exception as e:
        return False


accounts_increased_by_debits = [
    "ASSET",
    "EXPENSE",
]

accounts_increased_by_credits = [
    "LIABILITY",
    "EQUITY",
    "REVENUE",
]


def get_system_parameter(code):
    ...
    # return SystemParameters.objects.get(code=code)


from datetime import datetime, date

def to_datetime(val):
    if val is None:
        return None

    if isinstance(val, datetime):
        return val

    if isinstance(val, date):
        # promote to datetime at midnight
        return datetime.combine(val, datetime.min.time())

    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return datetime.strptime(val, "%Y-%m-%d")
    
    raise TypeError(f"Unsupported type for to_datetime(): {type(val)}")

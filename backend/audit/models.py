from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey("content_type", "object_id")

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True
    )
    institution = models.ForeignKey(
        'institution.Institution', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Institution associated with this audit log."
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(
        null=True, blank=True, help_text="Details of changes made (for updates)."
    )
    description = models.TextField(
        blank=True, help_text="Human-readable description of the action."
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=['institution', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} on {self.content_type.model} (ID: {self.object_id}) by {self.user} at {self.timestamp}"
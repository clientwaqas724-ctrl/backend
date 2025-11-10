# Notifications_App/models.py
import uuid
from django.db import models
from django.conf import settings   # so we can reference AUTH_USER_MODEL
######################################################################################################################################################
######################################################################################################################################################
class Notification(models.Model):
    """
    Stores user-specific notifications.
    Fields:
        • id: UUID primary key
        • user: ForeignKey to the custom User model
        • title: Short title for the notification
        • message: Full notification message
        • is_read: Whether the user has opened/read it
        • created_at: Timestamp of creation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to your custom User model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]  # newest first
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    def __str__(self):
        return f"{self.title} → {self.user.email}"
######################################################################################################################################################
######################################################################################################################################################

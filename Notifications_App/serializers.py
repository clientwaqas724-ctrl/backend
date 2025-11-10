from rest_framework import serializers
from .models import Notification
######################################################################################################################################################
######################################################################################################################################################
class NotificationSerializer(serializers.ModelSerializer):
    # Make every field required and give custom messages
    user = serializers.PrimaryKeyRelatedField(
        queryset=Notification._meta.get_field('user').related_model.objects.all(),
        required=True,
        error_messages={'required': 'User ID is required.'}
    )
    title = serializers.CharField(
        required=True,
        error_messages={'required': 'Title is required.'}
    )
    message = serializers.CharField(
        required=True,
        error_messages={'required': 'Message is required.'}
    )
    is_read = serializers.BooleanField(
        required=True,
        error_messages={'required': 'Read status (true/false) is required.'}
    )

    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']
######################################################################################################################################################
######################################################################################################################################################

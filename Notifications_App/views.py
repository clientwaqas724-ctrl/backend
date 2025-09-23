from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.exceptions import NotAuthenticated
#########################################################################################################################################################
#####################################################################################################################################################
class NotificationViewSet(viewsets.ModelViewSet):
    """
    Provides:
    - create (POST)
    - retrieve (GET /<id>/)
    - list + search (GET)
    - update/partial_update (PUT/PATCH)
    - destroy (DELETE)

    • No authentication required.
    • Anonymous users can read all notifications.
    • Create requests that omit 'user' will fail validation
      (because the serializer still requires a user field).
    """
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Anyone can view all notifications.
        """
        return Notification.objects.all()

    def perform_create(self, serializer):
        """
        Let the client explicitly provide the 'user' field
        (the serializer still requires it).
        """
        serializer.save()
#########################################################################################################################################################
#####################################################################################################################################################

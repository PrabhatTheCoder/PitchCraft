from rest_framework import filters, viewsets

from .models import MediaContact
from .serializers import MediaContactSerializer


class MediaContactViewSet(viewsets.ModelViewSet):
    """CRUD API for media contacts, with simple search over name/outlet/beat."""

    queryset = MediaContact.objects.all()
    serializer_class = MediaContactSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "outlet", "beat"]

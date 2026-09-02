from rest_framework import serializers

from .models import MediaContact


class MediaContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaContact
        fields = ["id", "name", "email", "outlet", "beat", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

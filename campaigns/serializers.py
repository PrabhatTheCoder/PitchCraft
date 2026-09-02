from rest_framework import serializers

from contacts.models import MediaContact

from .models import Campaign, Pitch


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ["id", "name", "client_name", "brief", "tone", "created_at"]
        read_only_fields = ["id", "created_at"]


class PitchSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)

    class Meta:
        model = Pitch
        fields = [
            "id", "campaign", "campaign_name", "contact", "contact_name",
            "subject", "body", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "subject", "body", "created_at", "updated_at"]


class GeneratePitchRequestSerializer(serializers.Serializer):
    campaign_id = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    contact_id = serializers.PrimaryKeyRelatedField(queryset=MediaContact.objects.all())

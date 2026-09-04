from rest_framework import serializers

from contacts.models import MediaContact

from .models import Campaign, Pitch
from .tasks import generate_pitch_task


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
            "subject", "body",
            "generation_status", "generation_error",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "subject", "body",
            "generation_status", "generation_error",
            "created_at", "updated_at",
        ]
        # DRF auto-derives a UniqueTogetherValidator from the model's
        # UniqueConstraint(campaign, contact) — that would reject a repost
        # as a 400 duplicate. We want the opposite: reposting the same pair
        # is how a consultant regenerates a pitch, handled via
        # get_or_create() in create() below.
        validators = []

    def validate_campaign(self, campaign):
        request = self.context["request"]
        if campaign.user_id != request.user.id:
            raise serializers.ValidationError("Campaign not found.")
        return campaign

    def validate_contact(self, contact):
        request = self.context["request"]
        if contact.user_id != request.user.id:
            raise serializers.ValidationError("Contact not found.")
        return contact

    def create(self, validated_data):
        # get_or_create: hitting POST again on an existing pair re-triggers
        # generation instead of raising a duplicate error — that's how a
        # consultant "regenerates" a pitch from the same form.
        pitch, _ = Pitch.objects.get_or_create(
            campaign=validated_data["campaign"],
            contact=validated_data["contact"],
        )
        pitch.mark_generating()
        generate_pitch_task.delay(pitch_id=str(pitch.id))
        return pitch


class GeneratePitchRequestSerializer(serializers.Serializer):
    campaign_id = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    contact_id = serializers.PrimaryKeyRelatedField(queryset=MediaContact.objects.all())

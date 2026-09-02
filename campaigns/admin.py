from django.contrib import admin

from .models import Campaign, Pitch


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "client_name", "tone", "created_at"]
    search_fields = ["name", "client_name"]


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ["campaign", "contact", "status", "updated_at"]
    list_filter = ["status", "campaign"]

from django.contrib import admin

from .models import MediaContact


@admin.register(MediaContact)
class MediaContactAdmin(admin.ModelAdmin):
    list_display = ["name", "outlet", "beat", "email"]
    search_fields = ["name", "outlet", "beat", "email"]

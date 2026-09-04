from django.urls import path

from campaigns.views import (
    campaign_detail,
    campaign_list_create,
    pitch_detail,
    pitch_list_create,
)


urlpatterns = [
    path("list-campaigns/", campaign_list_create,name="campaign-list-create",),
    path('create-campaigns/', campaign_list_create, name='create-campaign'),
    path("update-campaigns/<uuid:pk>/", campaign_detail, name="campaign-detail",),
    path("delete-campaigns/<uuid:pk>/", campaign_detail, name="campaign-detail",),
    
    path("create-pitches/", pitch_list_create, name="pitch-list-create",),
    path("pitches/", pitch_list_create, name="pitch-list-create",),
    path("pitches/<uuid:pk>/", pitch_detail, name="pitch-detail",),
]
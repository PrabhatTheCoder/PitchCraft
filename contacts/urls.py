from django.urls import path
from contacts.views import MediaContactListCreateView, MediaContactDetailView


urlpatterns = [
    # List contacts
    path("list-media-contacts/", MediaContactListCreateView.as_view(),name="media-contact-list",),

    # Create contact
    path("create-media-contacts/", MediaContactListCreateView.as_view(),name="media-contact-create",),

    # Get contact detail
    path("get-media-contacts/<uuid:pk>/", MediaContactDetailView.as_view(),name="media-contact-detail",),

    # Update contact
    path("update-media-contacts/<uuid:pk>/", MediaContactDetailView.as_view(),name="media-contact-update",),

    # Delete contact
    path("delete-media-contacts/<uuid:pk>/", MediaContactDetailView.as_view(),name="media-contact-delete",),
]
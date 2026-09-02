from rest_framework.routers import DefaultRouter

from .views import CampaignViewSet, PitchViewSet

router = DefaultRouter()
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("pitches", PitchViewSet, basename="pitch")

urlpatterns = router.urls

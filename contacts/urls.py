from rest_framework.routers import DefaultRouter

from .views import MediaContactViewSet

router = DefaultRouter()
router.register("contacts", MediaContactViewSet, basename="contact")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from .views import EvaluacionCreditoViewSet

router = DefaultRouter()
router.register("evaluaciones", EvaluacionCreditoViewSet, basename="evaluacion")

urlpatterns = router.urls

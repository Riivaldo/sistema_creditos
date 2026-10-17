from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EvaluacionCredito
from .serializers import (
    EvaluacionCreditoSerializer,
    GarantiaSerializer,
    ObservacionSerializer,
    RiesgoUpdateSerializer,
)


class EvaluacionCreditoViewSet(viewsets.ModelViewSet):
    """
    CRUD base (list, retrieve, create, update, destroy) en /api/evaluaciones/
    más las acciones específicas del módulo:

      PATCH /api/evaluaciones/{id}/riesgo/
      GET|POST /api/evaluaciones/{id}/garantias/
      GET|POST /api/evaluaciones/{id}/observaciones/
      GET  /api/evaluaciones/{id}/resultado/           -> consumido por apps/creditos (integrante 3)
      GET  /api/evaluaciones/por-solicitud/{id}/        -> consumido por apps/clientes_solicitudes (integrante 1)
    """

    queryset = EvaluacionCredito.objects.all().select_related(
        "solicitud", "evaluador"
    ).prefetch_related("garantias", "observaciones")
    serializer_class = EvaluacionCreditoSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=["patch"], url_path="riesgo")
    def actualizar_riesgo(self, request, pk=None):
        evaluacion = self.get_object()
        serializer = RiesgoUpdateSerializer(evaluacion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(EvaluacionCreditoSerializer(evaluacion, context={"request": request}).data)

    @action(detail=True, methods=["get", "post"], url_path="garantias")
    def garantias(self, request, pk=None):
        evaluacion = self.get_object()

        if request.method == "GET":
            serializer = GarantiaSerializer(evaluacion.garantias.all(), many=True)
            return Response(serializer.data)

        serializer = GarantiaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(evaluacion=evaluacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], url_path="observaciones")
    def observaciones(self, request, pk=None):
        evaluacion = self.get_object()

        if request.method == "GET":
            serializer = ObservacionSerializer(evaluacion.observaciones.all(), many=True)
            return Response(serializer.data)

        serializer = ObservacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # la observación se asocia siempre al evaluador autenticado (trazabilidad real)
        serializer.save(evaluacion=evaluacion, evaluador=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="resultado")
    def resultado(self, request, pk=None):
        """Resumen que consume apps/creditos, el módulo de aprobación (integrante 3)."""
        evaluacion = self.get_object()
        garantias = evaluacion.garantias.all()
        data = {
            "evaluacion_id": evaluacion.id,
            "solicitud_id": evaluacion.solicitud_id,
            "capacidad_pago": evaluacion.capacidad_pago,
            "nivel_riesgo": evaluacion.nivel_riesgo,
            "score_crediticio": evaluacion.score_crediticio,
            "estado": evaluacion.estado,
            "total_garantias": garantias.count(),
            "valor_total_garantias": sum((g.valor_estimado for g in garantias), start=0),
        }
        return Response(data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"por-solicitud/(?P<solicitud_id>\d+)",
    )
    def por_solicitud(self, request, solicitud_id=None):
        """Para que apps/clientes_solicitudes (integrante 1) consulte si
        una solicitud ya tiene evaluación y en qué estado está."""
        evaluacion = get_object_or_404(EvaluacionCredito, solicitud_id=solicitud_id)
        serializer = EvaluacionCreditoSerializer(evaluacion, context={"request": request})
        return Response(serializer.data)

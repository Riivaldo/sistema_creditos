from rest_framework import serializers

from apps.clientes_solicitudes.models import SolicitudCredito  # confirmar nombre de clase con integrante 1

from .models import EvaluacionCredito, Garantia, Observacion


class GarantiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garantia
        fields = ["id", "tipo", "descripcion", "valor_estimado", "creado"]
        read_only_fields = ["id", "creado"]

    def validate_valor_estimado(self, value):
        if value <= 0:
            raise serializers.ValidationError("El valor estimado debe ser mayor a 0.")
        return value


class ObservacionSerializer(serializers.ModelSerializer):
    evaluador_nombre = serializers.CharField(source="evaluador.get_full_name", read_only=True)

    class Meta:
        model = Observacion
        fields = ["id", "texto", "evaluador", "evaluador_nombre", "creado"]
        read_only_fields = ["id", "evaluador", "evaluador_nombre", "creado"]

    def validate_texto(self, value):
        if not value.strip():
            raise serializers.ValidationError("La observación no puede estar vacía.")
        return value


class EvaluacionCreditoSerializer(serializers.ModelSerializer):
    garantias = GarantiaSerializer(many=True, read_only=True)
    observaciones = ObservacionSerializer(many=True, read_only=True)
    solicitud_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = EvaluacionCredito
        fields = [
            "id",
            "solicitud",
            "solicitud_id",
            "evaluador",
            "ingreso_mensual",
            "gastos_mensuales",
            "capacidad_pago",
            "score_crediticio",
            "nivel_riesgo",
            "estado",
            "fecha_evaluacion",
            "actualizado",
            "garantias",
            "observaciones",
        ]
        read_only_fields = [
            "id",
            "solicitud",
            "evaluador",
            "capacidad_pago",
            "fecha_evaluacion",
            "actualizado",
            "garantias",
            "observaciones",
        ]

    def validate_solicitud_id(self, value):
        # 1) comprobar existencia de la solicitud (integración con módulo 1)
        if not SolicitudCredito.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No existe una solicitud de crédito con ese ID.")
        # 2) evitar duplicados: una solicitud solo puede tener una evaluación
        if EvaluacionCredito.objects.filter(solicitud_id=value).exists():
            raise serializers.ValidationError(
                "Esta solicitud ya tiene una evaluación crediticia registrada."
            )
        return value

    def validate(self, data):
        ingreso = data.get("ingreso_mensual")
        gastos = data.get("gastos_mensuales")
        if ingreso is not None and gastos is not None and gastos > ingreso:
            raise serializers.ValidationError(
                {"gastos_mensuales": "Los gastos no pueden superar el ingreso mensual."}
            )
        return data

    def create(self, validated_data):
        solicitud_id = validated_data.pop("solicitud_id")
        validated_data["solicitud_id"] = solicitud_id
        # el evaluador siempre se toma del usuario autenticado, nunca del cliente
        validated_data["evaluador"] = self.context["request"].user
        return super().create(validated_data)


class RiesgoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluacionCredito
        fields = ["nivel_riesgo", "score_crediticio", "estado"]

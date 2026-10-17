from django.conf import settings
from django.db import models

# Ajustar este import al nombre real de la app/módulo del integrante 1.
# Se asume una app "solicitudes" con un modelo SolicitudCredito.
from solicitudes.models import SolicitudCredito


class NivelRiesgo(models.TextChoices):
    BAJO = "BAJO", "Bajo"
    MEDIO = "MEDIO", "Medio"
    ALTO = "ALTO", "Alto"


class EstadoEvaluacion(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_REVISION = "EN_REVISION", "En revisión"
    OBSERVADA = "OBSERVADA", "Observada"
    FINALIZADA = "FINALIZADA", "Finalizada"


class EvaluacionCredito(models.Model):
    """Evaluación crediticia asociada 1 a 1 con una SolicitudCredito
    (módulo del integrante 1). El resultado se consume desde el módulo
    de aprobación (integrante 3) vía el endpoint /resultado/."""

    solicitud = models.OneToOneField(
        SolicitudCredito,
        on_delete=models.CASCADE,
        related_name="evaluacion_credito",
    )
    evaluador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evaluaciones_realizadas",
    )
    ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2)
    gastos_mensuales = models.DecimalField(max_digits=12, decimal_places=2)
    capacidad_pago = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    score_crediticio = models.PositiveIntegerField(null=True, blank=True)
    nivel_riesgo = models.CharField(
        max_length=10, choices=NivelRiesgo.choices, default=NivelRiesgo.MEDIO
    )
    estado = models.CharField(
        max_length=15, choices=EstadoEvaluacion.choices, default=EstadoEvaluacion.PENDIENTE
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_evaluacion"]

    def calcular_capacidad_pago(self):
        """capacidad_pago = ingreso - gastos.
        Ajustar la fórmula si la regla de negocio del grupo exige, p. ej.,
        un porcentaje máximo de endeudamiento sobre el ingreso."""
        return self.ingreso_mensual - self.gastos_mensuales

    def save(self, *args, **kwargs):
        self.capacidad_pago = self.calcular_capacidad_pago()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evaluación #{self.pk} - Solicitud #{self.solicitud_id}"


class Garantia(models.Model):
    class TipoGarantia(models.TextChoices):
        HIPOTECARIA = "HIPOTECARIA", "Hipotecaria"
        PRENDARIA = "PRENDARIA", "Prendaria"
        PERSONAL = "PERSONAL", "Personal / Aval"

    evaluacion = models.ForeignKey(
        EvaluacionCredito, on_delete=models.CASCADE, related_name="garantias"
    )
    tipo = models.CharField(max_length=15, choices=TipoGarantia.choices)
    descripcion = models.TextField()
    valor_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - Bs. {self.valor_estimado}"


class Observacion(models.Model):
    evaluacion = models.ForeignKey(
        EvaluacionCredito, on_delete=models.CASCADE, related_name="observaciones"
    )
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    texto = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"Observación de {self.evaluador} en evaluación #{self.evaluacion_id}"

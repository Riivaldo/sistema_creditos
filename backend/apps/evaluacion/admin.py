from django.contrib import admin
from .models import EvaluacionCredito, Garantia, Observacion

@admin.register(EvaluacionCredito)
class EvaluacionCreditoAdmin(admin.ModelAdmin):
    list_display = ["id", "solicitud", "evaluador", "capacidad_pago", "nivel_riesgo", "estado"]
    list_filter = ["nivel_riesgo", "estado"]

admin.site.register(Garantia)
admin.site.register(Observacion)

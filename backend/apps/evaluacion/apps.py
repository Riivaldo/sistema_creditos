from django.apps import AppConfig


class EvaluacionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.evaluacion"
    label = "evaluacion"  # mantiene las tablas/migraciones como evaluacion

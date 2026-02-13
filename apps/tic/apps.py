from django.apps import AppConfig

class TicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tic"

    def ready(self):
        # Importa signals no arranque do Django
        import apps.tic.signals  # noqa




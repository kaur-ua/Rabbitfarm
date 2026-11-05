from django.apps import AppConfig


class RabbitsConfig(AppConfig):
    name = "rabbits"

    def ready(self):
        import rabbits.signals

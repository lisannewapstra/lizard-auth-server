from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = 'lizard_auth_server'
    verbose_name = 'Lizard Auth Server'

    def ready(self):
        # Enable the signals
        from lizard_auth_server.signal_handlers import create_user_profile  # noqa

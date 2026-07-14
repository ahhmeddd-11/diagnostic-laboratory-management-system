from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Disconnect the standard update_last_login signal during user login events.
        # This keeps the Users database table schema fully read-only by avoiding
        # automatic 'last_login' column update attempts during user validation.
        from django.contrib.auth.models import update_last_login
        from django.contrib.auth.signals import user_logged_in
        try:
            user_logged_in.disconnect(update_last_login)
        except Exception:
            pass

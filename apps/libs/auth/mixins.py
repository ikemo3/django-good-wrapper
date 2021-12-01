from django.contrib.auth.mixins import LoginRequiredMixin
from social_django.models import UserSocialAuth


class Auth0LoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not request.user.is_authenticated:
                return self.handle_no_permission()

            request.user.social_auth.get(provider="auth0")
        except UserSocialAuth.DoesNotExist:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class NotRestrictedMixin:
    """アクセス制限がかかっていないことを表すMixin"""

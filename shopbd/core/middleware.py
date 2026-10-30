from django.conf import settings
from django.utils import translation


class DefaultLanguageMiddleware:
    """
    Visitors who have never chosen a language get the "Default language"
    set in Admin → Site Settings (instead of their browser language).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LANGUAGE_COOKIE_NAME not in request.COOKIES:
            from .models import SiteSetting
            try:
                lang = SiteSetting.load().default_language
            except Exception:  # database not ready yet (first migrate)
                lang = None
            if lang and lang in dict(settings.LANGUAGES):
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
        return self.get_response(request)

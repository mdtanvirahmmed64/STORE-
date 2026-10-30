"""
Content translation helpers.

Fixed website text (buttons, menus, messages) is translated with Django's
gettext + the files in /locale.  Text that the admin types (product names,
categories, banners, pages ...) is translated with small "<Model>Translation"
tables that the admin fills in from the Admin panel (inline "Translations").

Template usage:   {{ product|tr:"name" }}
If no translation exists for the current language, the original text is shown.
"""
from django.conf import settings
from django.utils.translation import get_language

DEFAULT_LANG = settings.LANGUAGE_CODE.split("-")[0]

# Languages offered in the "Translations" inline (all except the default one)
TRANSLATION_LANGUAGES = [(code, name) for code, name in settings.LANGUAGES if code != DEFAULT_LANG]


def current_lang():
    return (get_language() or DEFAULT_LANG).split("-")[0]


class TranslatableMixin:
    """Add to a model that has a related_name="translations" translation model."""

    def get_translation(self, lang=None):
        lang = lang or current_lang()
        if lang == DEFAULT_LANG or not self.pk:
            return None
        cache = getattr(self, "_translation_cache", None)
        if cache is None:
            # uses prefetch_related("translations") results when available
            cache = {t.language: t for t in self.translations.all()}
            self._translation_cache = cache
        return cache.get(lang)

    def tr(self, field):
        t = self.get_translation()
        value = getattr(t, field, "") if t else ""
        return value or getattr(self, field)

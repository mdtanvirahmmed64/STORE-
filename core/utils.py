from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def safe_redirect(request, url, fallback):
    """Redirect only to URLs on this site (prevents open-redirect attacks)."""
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return redirect(url)
    return redirect(fallback)

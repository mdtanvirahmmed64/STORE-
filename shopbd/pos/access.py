"""Who can use the shop counter (POS) and for which branch."""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Branch


def staff_record(user):
    return getattr(user, "branch_staff", None) if user.is_authenticated else None


def allowed_branches(user):
    """Superusers: every active branch. Branch staff: only their own branch."""
    if not user.is_authenticated:
        return Branch.objects.none()
    if user.is_superuser:
        return Branch.objects.filter(is_active=True)
    rec = staff_record(user)
    if rec:
        return Branch.objects.filter(pk=rec.branch_id, is_active=True)
    return Branch.objects.none()


def has_pos_access(user):
    return allowed_branches(user).exists()


def is_manager(user, branch=None):
    if user.is_superuser:
        return True
    rec = staff_record(user)
    return bool(rec and rec.role == "manager" and (branch is None or rec.branch_id == branch.id))


def can_see_all_branches(user):
    return user.is_superuser


def pos_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not has_pos_access(request.user):
            raise PermissionDenied("You are not assigned to any branch.")
        return view(request, *args, **kwargs)
    return wrapper


def current_branch(request):
    """Branch chosen in the top bar (remembered in the session)."""
    branches = allowed_branches(request.user)
    wanted = request.GET.get("branch") or request.session.get("pos_branch")
    branch = branches.filter(pk=wanted).first() if str(wanted or "").isdigit() else None
    branch = branch or branches.first()
    if branch:
        request.session["pos_branch"] = branch.pk
    return branch

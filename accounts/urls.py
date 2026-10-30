from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.utils.translation import gettext_lazy as _

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("addresses/", views.address_list, name="addresses"),
    path("addresses/add/", views.address_form, name="address_add"),
    path("addresses/<int:pk>/edit/", views.address_form, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),

    path("password/change/", auth_views.PasswordChangeView.as_view(
        template_name="accounts/password_change.html",
        success_url=reverse_lazy("accounts:password_change_done")), name="password_change"),
    path("password/change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/simple_message.html",
        extra_context={"title": _("Password changed"), "text": _("Your password has been changed successfully.")}),
        name="password_change_done"),

    path("password/reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.txt",
        success_url=reverse_lazy("accounts:password_reset_done")), name="password_reset"),
    path("password/reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/simple_message.html",
        extra_context={"title": _("Check your email"),
                       "text": _("If an account exists with that email, we have sent a password reset link.")}),
        name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete")), name="password_reset_confirm"),
    path("password/reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/simple_message.html",
        extra_context={"title": _("Password reset complete"), "text": _("You can now login with your new password.")}),
        name="password_reset_complete"),
]

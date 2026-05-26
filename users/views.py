from urllib.parse import urlencode

from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.views import LogoutView as AuthLogoutView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import CreateView, TemplateView

from .forms import UserRegistrationForm

User = get_user_model()


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "users/register.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        if self.object.role == 'pasajero':
            return reverse("trips:search")
        return reverse("home")


class LoginView(AuthLoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.role == 'pasajero':
            return reverse("trips:search")
        return reverse("home")


class LogoutView(AuthLogoutView):
    next_page = reverse_lazy("users:login")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"


class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset_form.html"
    success_url = reverse_lazy("users:password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        users = list(form.get_users(email))
        if users:
            user = users[0]
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse("users:password_reset_confirm", kwargs={
                    "uidb64": uid,
                    "token": token,
                })
            )
            success_url = self.get_success_url()
            return self.redirect_to_done(reset_url, success_url)
        return self.redirect_to_done(None, self.get_success_url())

    def redirect_to_done(self, reset_url, success_url):
        from django.http import HttpResponseRedirect
        if reset_url:
            return HttpResponseRedirect(f"{success_url}?reset_url={urlencode({'url': reset_url})}")
        return HttpResponseRedirect(success_url)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"

    def get_context_data(self, **kwargs):
        from urllib.parse import parse_qs
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("reset_url", "")
        if query:
            parsed = parse_qs(query)
            context["reset_url"] = parsed.get("url", [None])[0]
        return context

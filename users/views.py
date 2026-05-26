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


from django.contrib import messages
from django.views.generic.edit import FormView
from .forms import UserRegistrationForm, DirectPasswordResetForm

class DirectPasswordResetView(FormView):
    template_name = "users/password_reset_form.html"
    form_class = DirectPasswordResetForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        username = form.cleaned_data["username"]
        new_password = form.cleaned_data["new_password"]
        
        # Encontramos al usuario (el form.clean() ya validó que existe)
        user = User.objects.get(email=email, username=username)
        user.set_password(new_password)
        user.save()
        
        messages.success(self.request, "Tu contraseña ha sido restablecida exitosamente. Ahora puedes iniciar sesión.")
        return super().form_valid(form)

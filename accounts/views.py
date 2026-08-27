from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import RegisterForm
from .models import Role


def register(request):
    """Create a Reader, Journalist, or Editor account and sign it in."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome, {user.username}. Your {user.get_role_display()} account is ready.",
            )
            return redirect("accounts:dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def role_required(role):
    """Restrict a view to a single application role (superusers are allowed)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role == role:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have access to this dashboard.")

        return wrapped

    return decorator


@login_required
def dashboard(request):
    """Send each authenticated user to the dashboard for their selected role."""
    if request.user.is_superuser:
        return redirect("accounts:editor_dashboard")
    if request.user.role == Role.READER:
        return redirect("accounts:reader_dashboard")
    if request.user.role == Role.JOURNALIST:
        return redirect("accounts:journalist_dashboard")
    if request.user.role == Role.EDITOR:
        return redirect("accounts:editor_dashboard")
    return redirect("articles:article_list")


@role_required(Role.READER)
def reader_dashboard(request):
    return render(request, "accounts/reader_dashboard.html")


@role_required(Role.JOURNALIST)
def journalist_dashboard(request):
    return render(request, "accounts/journalist_dashboard.html")


@role_required(Role.EDITOR)
def editor_dashboard(request):
    return render(request, "accounts/editor_dashboard.html")

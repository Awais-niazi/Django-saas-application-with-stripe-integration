from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home_view")

    context = {}
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = None

        context["entered_username"] = username
        if not username or not password:
            context["error"] = "Username and password are required."
            return render(request, "auth/login.html", context)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home_view")

        context["error"] = "Invalid username or password."
        return render(request, "auth/login.html", context)

    return render(request, "auth/login.html", context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home_view")

    context = {}
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""

        context.update(
            {
                "entered_username": username,
                "entered_email": email,
            }
        )

        if not username or not email or not password:
            context["error"] = "Username, email, and password are required."
            return render(request, "auth/register.html", context)

        if User.objects.filter(username__iexact=username).exists():
            context["error"] = "That username is already taken."
            return render(request, "auth/register.html", context)

        if User.objects.filter(email__iexact=email).exists():
            context["error"] = "That email is already in use."
            return render(request, "auth/register.html", context)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        login(request, user)
        return redirect("home_view")

    return render(request, "auth/register.html", context)

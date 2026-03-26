from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import UserProfile
from .forms import UserProfileForm


# ✅ Home page
def home(request):
    return render(request, "home.html")


# ✅ Profile creation
@login_required
def create_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # If profile already exists → go directly to video
    if not created:
        return redirect('/video/')

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_online = True
            profile.save()

            return redirect('/video/')   # ✅ FINAL REDIRECT

    else:
        form = UserProfileForm(instance=profile)

    return render(request, "profile.html", {"form": form})


# ✅ Logout
def logout_user(request):
    logout(request)
    return redirect('/accounts/login/')
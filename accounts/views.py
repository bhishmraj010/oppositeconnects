from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import UserProfile
from .forms import UserProfileForm


# Home page
def home(request):
    profile = None
    friends = []

    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()

        from friends.models import Friendship
        friendships = Friendship.for_user(request.user).select_related("user1", "user2")
        friends = [f.other(request.user) for f in friendships]

    return render(request, "home.html", {"profile": profile, "friends": friends})


# Profile creation
@login_required
def create_profile(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    # Only skip the form if a REAL profile (name actually filled) exists.
    if profile and profile.name:
        return redirect('/video/')

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.is_online = True
            profile.save()

            return redirect('/video/')

    else:
        form = UserProfileForm(instance=profile)

    return render(request, "profile.html", {"form": form})


# Logout
def logout_user(request):
    logout(request)
    return redirect('/accounts/login/')
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import UserProfileForm

def home(request):
    return render(request, "home.html")




@login_required
def create_profile(request):

    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        form = UserProfileForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_online = True
            profile.save()

            return redirect('/video/')

    else:
        form = UserProfileForm(instance=profile)

    return render(request, "profile.html", {"form": form})
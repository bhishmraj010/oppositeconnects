from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile

@login_required
def video_chat(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None
    return render(request, "videochat.html", {"profile": profile})
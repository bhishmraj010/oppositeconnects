from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile

waiting_user = None

@login_required
def video_chat(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, "videochat.html", {"profile": profile})

def find_match(request):
    global waiting_user

    if waiting_user is None:
        waiting_user = request.user
        return JsonResponse({"status": "waiting"})
    else:
        partner = waiting_user
        waiting_user = None

        return JsonResponse({
            "status": "matched",
            "partner": partner.username
        })
import random
from django.http import JsonResponse
from accounts.models import UserProfile

def find_match(request):

    user_profile = UserProfile.objects.get(user=request.user)

    if user_profile.gender == "Male":
        strangers = UserProfile.objects.filter(
            gender="Female",
            is_online=True
        ).exclude(user=request.user)

    else:
        strangers = UserProfile.objects.filter(
            gender="Male",
            is_online=True
        ).exclude(user=request.user)

    if strangers.exists():

        stranger = random.choice(strangers)

        return JsonResponse({
            "match": stranger.user.username
        })

    return JsonResponse({
        "match": None
    })
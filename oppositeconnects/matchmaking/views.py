from django.http import JsonResponse

waiting_user = None

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
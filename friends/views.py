from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import FriendRequest, Friendship, Message

PRESENCE_TIMEOUT = 30  # seconds — matches the 15s heartbeat interval on the frontend


@login_required
def friends_list(request):
    friendships = Friendship.for_user(request.user).select_related("user1", "user2")
    friends = [f.other(request.user) for f in friendships]

    incoming = FriendRequest.objects.filter(
        to_user=request.user, status=FriendRequest.STATUS_PENDING
    ).select_related("from_user")

    outgoing = FriendRequest.objects.filter(
        from_user=request.user, status=FriendRequest.STATUS_PENDING
    ).select_related("to_user")

    return render(
        request,
        "friends/friends_list.html",
        {"friends": friends, "incoming": incoming, "outgoing": outgoing},
    )


@login_required
@require_POST
def send_request(request, username):
    to_user = get_object_or_404(User, username=username)

    if to_user == request.user:
        return JsonResponse({"status": "error", "message": "Can't friend yourself."}, status=400)

    if Friendship.are_friends(request.user, to_user):
        return JsonResponse({"status": "already_friends"})

    fr, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user, defaults={"status": FriendRequest.STATUS_PENDING}
    )
    if not created and fr.status == FriendRequest.STATUS_REJECTED:
        fr.status = FriendRequest.STATUS_PENDING
        fr.save(update_fields=["status", "updated_at"])

    return JsonResponse({"status": "sent", "request_id": fr.id})


@login_required
@require_POST
def respond_request(request, request_id):
    accept = request.POST.get("accept") == "1"
    fr = get_object_or_404(
        FriendRequest, id=request_id, to_user=request.user, status=FriendRequest.STATUS_PENDING
    )

    if accept:
        fr.status = FriendRequest.STATUS_ACCEPTED
        fr.save(update_fields=["status", "updated_at"])
        Friendship.create(fr.from_user, fr.to_user)
        return JsonResponse({"status": "accepted"})
    else:
        fr.status = FriendRequest.STATUS_REJECTED
        fr.save(update_fields=["status", "updated_at"])
        return JsonResponse({"status": "rejected"})


@login_required
@require_POST
def heartbeat(request):
    cache.set(f"online:{request.user.username}", True, timeout=PRESENCE_TIMEOUT)
    return JsonResponse({"status": "ok"})


@login_required
def online_status(request):
    friendships = Friendship.for_user(request.user).select_related("user1", "user2")
    friend_usernames = [f.other(request.user).username for f in friendships]
    online = [u for u in friend_usernames if cache.get(f"online:{u}")]

    return JsonResponse({"online": online})


@login_required
def message_thread(request, username):
    other = get_object_or_404(User, username=username)

    if not Friendship.are_friends(request.user, other):
        return JsonResponse({"status": "error", "message": "Not friends."}, status=403)

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if request.method == "POST":
        text = request.POST.get("text", "").strip()[:1000]
        if text:
            Message.objects.create(sender=request.user, receiver=other, text=text)
        if is_ajax:
            return JsonResponse({"status": "sent"})
        return redirect("message_thread", username=username)

    # Mark incoming messages as read when the thread is opened.
    Message.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user)
    )

    if is_ajax:
        return JsonResponse({
            "messages": [
                {
                    "text": m.text,
                    "mine": m.sender_id == request.user.id,
                    "time": m.created_at.strftime("%H:%M"),
                }
                for m in messages
            ]
        })

    return render(request, "friends/message_thread.html", {"other": other, "messages": messages})
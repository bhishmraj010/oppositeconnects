import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import BannedIP

waiting_pools = {
    "Male":   [],
    "Female": [],
    "Other":  [],
}

OPPOSITE = {
    "Male":   "Female",
    "Female": "Male",
    "Other":  "Other",
}

# username -> connected VideoConsumer instance (for direct "call a friend")
online_users = {}


@database_sync_to_async
def is_banned(ip: str) -> bool:
    return BannedIP.objects.filter(ip_address=ip).exists()


@database_sync_to_async
def ban_ip(ip: str, reason: str = "Vulgar activity reported by peer"):
    BannedIP.objects.get_or_create(ip_address=ip, defaults={"reason": reason})


@database_sync_to_async
def create_or_refresh_friend_request(from_user, to_user):
    from friends.models import FriendRequest, Friendship

    if Friendship.are_friends(from_user, to_user):
        return None, "already_friends"

    fr, created = FriendRequest.objects.get_or_create(
        from_user=from_user, to_user=to_user,
        defaults={"status": FriendRequest.STATUS_PENDING},
    )
    if not created and fr.status == FriendRequest.STATUS_REJECTED:
        fr.status = FriendRequest.STATUS_PENDING
        fr.save(update_fields=["status", "updated_at"])
    return fr, "sent"


@database_sync_to_async
def accept_or_reject_friend_request(request_id, to_user, accept):
    from friends.models import FriendRequest, Friendship

    try:
        fr = FriendRequest.objects.get(
            id=request_id, to_user=to_user, status=FriendRequest.STATUS_PENDING
        )
    except FriendRequest.DoesNotExist:
        return None

    if accept:
        fr.status = FriendRequest.STATUS_ACCEPTED
        fr.save(update_fields=["status", "updated_at"])
        Friendship.create(fr.from_user, fr.to_user)
    else:
        fr.status = FriendRequest.STATUS_REJECTED
        fr.save(update_fields=["status", "updated_at"])
    return fr


def get_client_ip(scope) -> str:
    headers = dict(scope.get("headers", []))
    forwarded = headers.get(b"x-forwarded-for", b"").decode()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return scope.get("client", ("unknown", 0))[0]


class VideoConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user    = self.scope.get("user")
        self.ip      = get_client_ip(self.scope)
        self.gender  = None
        self.partner = None

        # Video chat requires a logged-in user (needed for friend requests / bans).
        if self.user is None or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        if await is_banned(self.ip):
            await self.close(code=4003)
            return

        await self.accept()
        online_users[self.user.username] = self
        await self.send(text_data=json.dumps({"type": "need_gender"}))

    async def receive(self, text_data):
        data     = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "register":
            gender = data.get("gender", "Other")
            if gender not in waiting_pools:
                gender = "Other"
            self.gender = gender
            if data.get("mode") == "call":
                return
            await self._try_match()
            return

        if msg_type == "call_friend":
            target_username = data.get("username")
            target = online_users.get(target_username)

            if (
                not target
                or target is self
                or target.partner is not None
                or self.partner is not None
            ):
                await self.send(text_data=json.dumps({
                    "type": "call_failed",
                    "reason": "offline_or_busy",
                }))
                return

            for pool in waiting_pools.values():
                if self in pool:
                    pool.remove(self)
                if target in pool:
                    pool.remove(target)

            self.partner   = target
            target.partner = self

            await self.send(text_data=json.dumps({
                "type":             "start",
                "partner_gender":   target.gender or "Other",
                "partner_username": target.user.username,
                "is_caller":        True,
                "direct_call":      True,
            }))
            await target.send(text_data=json.dumps({
                "type":             "start",
                "partner_gender":   self.gender or "Other",
                "partner_username": self.user.username,
                "is_caller":        False,
                "direct_call":      True,
            }))
            return

        if msg_type == "report":
            if self.partner:
                await ban_ip(self.partner.ip, reason="Reported for vulgar activity")
                await self.partner.send(text_data=json.dumps({"type": "banned"}))
                await self.partner.close(code=4003)
                await self.send(text_data=json.dumps({"type": "partner_banned"}))
                self.partner.partner = None
                self.partner = None
            return

        if msg_type == "chat":
            if self.partner:
                message = str(data.get("message", ""))[:500].strip()
                if message:
                    await self.partner.send(text_data=json.dumps({
                        "type":    "chat",
                        "message": message,
                        "from":    self.user.username,
                    }))
            return

        if msg_type == "friend_request":
            if self.partner and self.partner.user and self.partner.user.is_authenticated:
                fr, status = await create_or_refresh_friend_request(self.user, self.partner.user)
                if status == "already_friends":
                    await self.send(text_data=json.dumps({"type": "friend_request_result", "status": "already_friends"}))
                elif fr:
                    await self.partner.send(text_data=json.dumps({
                        "type":         "friend_request_received",
                        "from_username": self.user.username,
                        "request_id":    fr.id,
                    }))
                    await self.send(text_data=json.dumps({"type": "friend_request_result", "status": "sent"}))
            return

        if msg_type == "friend_request_response":
            request_id = data.get("request_id")
            accept     = bool(data.get("accept"))
            fr = await accept_or_reject_friend_request(request_id, self.user, accept)
            if fr and self.partner:
                await self.partner.send(text_data=json.dumps({
                    "type":   "friend_request_accepted" if accept else "friend_request_declined",
                    "by":     self.user.username,
                }))
            return

        if self.partner:
            await self.partner.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        if self.gender and self.gender in waiting_pools:
            pool = waiting_pools[self.gender]
            if self in pool:
                pool.remove(self)

        if getattr(self, "user", None) and self.user.is_authenticated:
            if online_users.get(self.user.username) is self:
                del online_users[self.user.username]

        if self.partner:
            try:
                await self.partner.send(text_data=json.dumps({"type": "disconnect"}))
            except Exception:
                pass
            self.partner.partner = None
            self.partner = None

    async def _try_match(self):
        if not self.gender or self.gender not in waiting_pools:
            self.gender = "Other"

        preferred = OPPOSITE.get(self.gender, "Other")

        fallback_order = []
        for k in [preferred, "Other", self.gender]:
            if k in waiting_pools and k not in fallback_order:
                fallback_order.append(k)

        partner = None
        for pool_key in fallback_order:
            pool = waiting_pools[pool_key]
            for candidate in pool:
                if candidate is not self:
                    partner = candidate
                    break
            if partner:
                pool.remove(partner)
                break

        if partner is None:
            if self not in waiting_pools[self.gender]:
                waiting_pools[self.gender].append(self)
            await self.send(text_data=json.dumps({"type": "waiting"}))
            return

        self.partner    = partner
        partner.partner = self

        await self.send(text_data=json.dumps({
            "type":            "start",
            "partner_gender":  partner.gender,
            "partner_username": partner.user.username,
            "is_caller":       True,
        }))

        await partner.send(text_data=json.dumps({
            "type":            "start",
            "partner_gender":  self.gender,
            "partner_username": self.user.username,
            "is_caller":       False,
        }))
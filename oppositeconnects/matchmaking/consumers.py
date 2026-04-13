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


@database_sync_to_async
def is_banned(ip: str) -> bool:
    return BannedIP.objects.filter(ip_address=ip).exists()


@database_sync_to_async
def ban_ip(ip: str, reason: str = "Vulgar activity reported by peer"):
    BannedIP.objects.get_or_create(ip_address=ip, defaults={"reason": reason})


def get_client_ip(scope) -> str:
    headers = dict(scope.get("headers", []))
    forwarded = headers.get(b"x-forwarded-for", b"").decode()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return scope.get("client", ("unknown", 0))[0]


class VideoConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.ip      = get_client_ip(self.scope)
        self.gender  = None
        self.partner = None

        if await is_banned(self.ip):
            await self.close(code=4003)
            return

        await self.accept()
        await self.send(text_data=json.dumps({"type": "need_gender"}))

    async def receive(self, text_data):
        data     = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "register":
            gender = data.get("gender", "Other")
            # ✅ Gender valid hai toh hi set karo
            if gender not in waiting_pools:
                gender = "Other"
            self.gender = gender
            await self._try_match()
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

        if self.partner:
            await self.partner.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        # ✅ Gender None ya invalid ho toh crash nahi hoga
        if self.gender and self.gender in waiting_pools:
            pool = waiting_pools[self.gender]
            if self in pool:
                pool.remove(self)

        if self.partner:
            try:
                await self.partner.send(text_data=json.dumps({"type": "disconnect"}))
            except Exception:
                pass
            self.partner.partner = None
            self.partner = None

    async def _try_match(self):
        # ✅ Gender None ya invalid hone ki koi chance nahi ab
        if not self.gender or self.gender not in waiting_pools:
            self.gender = "Other"

        preferred      = OPPOSITE.get(self.gender, "Other")
        # ✅ Sirf valid pool keys use karo
        fallback_order = [
            k for k in [preferred, "Other", self.gender]
            if k in waiting_pools
        ]

        partner = None
        for pool_key in fallback_order:
            pool = waiting_pools[pool_key]
            # ✅ Khud se match mat ho
            if pool and pool[0] is not self:
                partner = pool.pop(0)
                break

        if partner is None:
            # Waiting pool mein add karo agar pehle se nahi hai
            if self not in waiting_pools[self.gender]:
                waiting_pools[self.gender].append(self)
            await self.send(text_data=json.dumps({"type": "waiting"}))
            return

        self.partner    = partner
        partner.partner = self

        await self.send(text_data=json.dumps({
            "type":           "start",
            "partner_gender": partner.gender,
            "is_caller":      True,
        }))

        await partner.send(text_data=json.dumps({
            "type":           "start",
            "partner_gender": self.gender,
            "is_caller":      False,
        }))
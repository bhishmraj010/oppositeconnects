import json
from channels.generic.websocket import AsyncWebsocketConsumer

waiting_users = []

class VideoConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        await self.accept()

        if waiting_users:

            partner = waiting_users.pop()

            self.partner = partner
            partner.partner = self

            # send start signal to both
            await self.send(text_data=json.dumps({
                "type": "start"
            }))

            await partner.send(text_data=json.dumps({
                "type": "start"
            }))

        else:

            waiting_users.append(self)


    async def receive(self, text_data):

        data = json.loads(text_data)

        # forward message to partner
        if hasattr(self, "partner"):

            await self.partner.send(
                text_data=json.dumps(data)
            )


    async def disconnect(self, close_code):

        # remove from waiting list if still waiting
        if self in waiting_users:
            waiting_users.remove(self)

        # notify partner if connected
        if hasattr(self, "partner"):

            await self.partner.send(text_data=json.dumps({
                "type": "disconnect"
            }))
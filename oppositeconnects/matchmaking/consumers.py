import json
from channels.generic.websocket import AsyncWebsocketConsumer

waiting_user = None


class VideoConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        global waiting_user

        await self.accept()

        if waiting_user is None:
            waiting_user = self
            self.partner = None
        else:
            self.partner = waiting_user
            waiting_user.partner = self

            waiting_user = None


    async def receive(self, text_data):

        data = json.loads(text_data)

        if hasattr(self, "partner") and self.partner:
            await self.partner.send(text_data=json.dumps(data))


    async def disconnect(self, close_code):

        if hasattr(self, "partner") and self.partner:
            await self.partner.close()
# Futur : Django Channels pour WebSockets
# Quand activé, remplacer le polling AJAX par des connexions temps réel

# from channels.generic.websocket import AsyncJsonWebsocketConsumer
# from channels.db import database_sync_to_async
#
#
# class ChatConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
#         self.room_group_name = f'chat_{self.conversation_id}'
#
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name,
#         )
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name,
#         )
#
#     async def receive_json(self, content):
#         message = await self.create_message(content['content'])
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': {
#                     'id': str(message.id),
#                     'content': message.content,
#                     'sender': message.sender.full_name,
#                     'created_at': message.created_at.isoformat(),
#                 },
#             },
#         )
#
#     async def chat_message(self, event):
#         await self.send_json(event['message'])
#
#     @database_sync_to_async
#     def create_message(self, content):
#         from apps.messaging.models import Message, Conversation
#         from django.contrib.auth import get_user_model
#
#         conversation = Conversation.objects.get(id=self.conversation_id)
#         return Message.objects.create(
#             conversation=conversation,
#             sender=self.scope['user'],
#             content=content,
#         )

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs'].get('room_name')
        self.room_group_name = f'room_{self.room_name}'

        # Add the user to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Update user count
        await self.update_user_count(increment=True)

    async def disconnect(self, close_code):
        # Remove the user from the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Update user count
        await self.update_user_count(increment=False)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        sender_username = text_data_json.get('sender', '')
        reply_to_id = text_data_json.get('reply_to_id', '')

        # Save the message to the database
        message_data = await self.create_message({
            'message': message_content,
            'sender': sender_username,
            'reply_to_id': reply_to_id
        })

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_message',
                'message': message_data
            }
        )

    async def send_message(self, event):
        message_data = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message_data
        }))

    @database_sync_to_async
    def create_message(self, data):
        try:
            # Fetch room and sender instances
            room = Room.objects.get(room_name=self.room_name)
            sender = User.objects.get(username=data['sender'])

            # Handle the reply-to logic
            parent_message = None
            if 'reply_to_id' in data and data['reply_to_id']:
                try:
                    parent_message = Message.objects.get(id=data['reply_to_id'])
                except Message.DoesNotExist:
                    print(f"Message with id {data['reply_to_id']} does not exist.")

            # Create and save the message
            message = Message.objects.create(
                room=room,
                sender=sender,
                message=data['message'],
                parent_message=parent_message  # Save the parent message reference if available
            )

            # Return message data including timestamp for WebSocket
            return {
                'sender': sender.username,
                'message': message.message,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Format timestamp
                'reply_to_id': data.get('reply_to_id', '')
            }
        except Room.DoesNotExist:
            # Handle the case where the room does not exist
            print(f"Room with name {self.room_name} does not exist.")
        except User.DoesNotExist:
            # Handle the case where the user does not exist
            print(f"User with username {data['sender']} does not exist.")
        except Exception as e:
            # Handle any other exceptions
            print(f"Error creating message: {e}")
            return None

    async def update_user_count(self, increment):
        """Update and broadcast the current user count in the room."""
        cache_key = f'{self.room_group_name}_users'
        current_count = cache.get(cache_key, 0)

        if increment:
            new_count = current_count + 1
        else:
            new_count = current_count - 1 if current_count > 0 else 0

        cache.set(cache_key, new_count)

        # Broadcast the new count to all users in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count',
                'count': new_count,
            }
        )

    async def user_count(self, event):
        count = event['count']
        # Send the current user count to the WebSocket
        await self.send(text_data=json.dumps({
            'user_count': count
        }))

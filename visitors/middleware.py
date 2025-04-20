import jwt
from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware  # FIXED IMPORT
from django.conf import settings
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError  # FIXED TOKEN EXCEPTIONS
from channels.db import database_sync_to_async


User = get_user_model()

class WebSocketJWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope['query_string'].decode())

        token = query_string.get("token", [None])[0]
        if token:
            try:
                access_token = AccessToken(token)
                user = await self.get_user(access_token)
                scope['user'] = user
            except TokenError:  # FIXED ERROR HANDLING
                scope['user'] = None
        else:
            scope['user'] = None

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, access_token):
        return User.objects.get(id=access_token.payload['user_id'])  # FIXED PAYLOAD ACCESS
import os
import asyncio
import logging
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, EventSubSubscriptionType
from dotenv import load_dotenv
from models import db, TwitchUser
from server import app

load_dotenv()

TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')
TWITCH_REFRESH_TOKEN = os.getenv('TWITCH_REFRESH_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

logging.basicConfig(level=logging.INFO)


async def on_stream_online(event):
    user_id = event.event.broadcaster_user_id
    with app.app_context():
        user = TwitchUser.query.filter_by(username=event.event.broadcaster_user_login).first()
        if user:
            user.is_live = True
            db.session.commit()
            logging.info(f"🔴 {user.username} went live!")
            # Optional: trigger Discord webhook or UI refresh


async def on_stream_offline(event):
    user_id = event.event.broadcaster_user_id
    with app.app_context():
        user = TwitchUser.query.filter_by(username=event.event.broadcaster_user_login).first()
        if user:
            user.is_live = False
            db.session.commit()
            logging.info(f"⚫ {user.username} went offline.")


async def on_channel_update(event):
    user_id = event.event.broadcaster_user_id
    new_title = event.event.title
    new_game = event.event.category_name
    with app.app_context():
        user = TwitchUser.query.filter_by(username=event.event.broadcaster_user_login).first()
        if user:
            user.stream_title = new_title
            user.game_name = new_game
            db.session.commit()
            logging.info(f"🔁 {user.username} updated stream: {new_title} ({new_game})")


async def run_monitor():
    twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    await twitch.set_user_authentication(TWITCH_ACCESS_TOKEN, [
        AuthScope.CHANNEL_READ_STREAMING,
        AuthScope.CHANNEL_MANAGE_BROADCAST,
    ], TWITCH_REFRESH_TOKEN)

    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    with app.app_context():
        users = TwitchUser.query.all()
        for user in users:
            user_info = await twitch.get_users(logins=[user.username])
            if user_info['data']:
                user_id = user_info['data'][0]['id']
                await eventsub.listen_stream_online(user_id, on_stream_online)
                await eventsub.listen_stream_offline(user_id, on_stream_offline)
                await eventsub.listen_channel_update(user_id, on_channel_update)
                logging.info(f"Subscribed to events for {user.username}")

    while True:
        await asyncio.sleep(3600)


if __name__ == '__main__':
    asyncio.run(run_monitor())

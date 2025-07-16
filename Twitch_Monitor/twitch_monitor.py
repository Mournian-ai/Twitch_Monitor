import os
import requests
import asyncio
import logging
import aiohttp
from models import db, TwitchUser
from app import app
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_game_name_and_image(game_id, session):
    """Fetch the game name and box art from Twitch API using the game ID."""
    try:
        response = await session.get(
            f"https://api.twitch.tv/helix/games?id={game_id}",
            headers={
                'Client-ID': TWITCH_CLIENT_ID,
                'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}',
            },
        )
        game_data = await response.json()
        if game_data['data']:
            game_name = game_data['data'][0]['name']
            game_image = game_data['data'][0]['box_art_url'].replace("{width}x{height}", "40x40")
            return game_name, game_image
    except Exception as e:
        logging.error(f"Error fetching game info for game_id {game_id}: {e}")
    return "Unknown Game", ""

async def check_stream_status(username, session):
    """Check the live status, stream title, and game name/image for a Twitch user."""
    try:
        # Fetch user information
        user_response = await session.get(
            f"https://api.twitch.tv/helix/users?login={username}",
            headers={
                'Client-ID': TWITCH_CLIENT_ID,
                'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}',
            },
        )
        user_data = await user_response.json()

        if not user_data['data']:
            logging.warning(f"User {username} not found on Twitch.")
            return

        user_id = user_data['data'][0]['id']

        # Check if the user is live
        stream_response = await session.get(
            f"https://api.twitch.tv/helix/streams?user_id={user_id}",
            headers={
                'Client-ID': TWITCH_CLIENT_ID,
                'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}',
            },
        )
        stream_data = await stream_response.json()
        is_live = len(stream_data['data']) > 0

        stream_title = ""
        game_name = ""
        game_image = ""  # Initialize game_image here

        if is_live:
            stream_title = stream_data['data'][0]['title']
            game_id = stream_data['data'][0]['game_id']
            game_name, game_image = await fetch_game_name_and_image(game_id, session)

        # Update the database and send notifications if needed
        with app.app_context():
            user = TwitchUser.query.filter_by(username=username).first()
            if user:
                # Check if the user just went live
                if is_live and not user.is_live:
                    send_discord_notification(username, game_name)  # Send notification

                user.is_live = is_live
                user.stream_title = stream_title
                user.game_name = game_name
                user.game_image_url = game_image  # Ensure this is updated correctly
                db.session.commit()

        logging.info(f"Updated {username}: {'Live' if is_live else 'Offline'} - {game_name}")

    except Exception as e:
        logging.error(f"Error checking status for {username}: {e}")


async def monitor_twitch_users():
    """Monitor Twitch users' live statuses."""
    while True:
        logging.info("Checking Twitch user statuses...")
        with app.app_context():
            usernames = [user.username for user in TwitchUser.query.all()]

        async with aiohttp.ClientSession() as session:
            tasks = [check_stream_status(username, session) for username in usernames]
            await asyncio.gather(*tasks)

        logging.info("Sleeping for 5 minutes...")
        await asyncio.sleep(300)

def send_discord_notification(username, game_name):
    """Send a Discord notification when a user goes live."""
    if not DISCORD_WEBHOOK_URL:
        logging.warning("Discord webhook URL not set. Skipping notification.")
        return

    message = f"🎉 **{username}** is now live playing **{game_name}**! Watch here: https://www.twitch.tv/{username}"
    data = {
        "content": message
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logging.info(f"Discord notification sent for {username}.")
        else:
            logging.error(f"Failed to send Discord notification for {username}. Status: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending Discord notification for {username}: {e}")

def main():
    """Run the Twitch monitor."""
    try:
        asyncio.run(monitor_twitch_users())
    except KeyboardInterrupt:
        logging.info("Twitch monitor stopped.")

if __name__ == "__main__":
    main()

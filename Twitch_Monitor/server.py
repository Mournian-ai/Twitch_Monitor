from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, TwitchUser  # Import your database and model
from dotenv import load_dotenv, dotenv_values, set_key
import aiohttp
import asyncio
import os

load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Update if needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Admin password for protected actions
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Twitch API credentials (replace with your actual values)
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')


async def fetch_profile_image(username):
    """Fetch the profile image of a Twitch user using the Twitch API."""
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.get(
                f"https://api.twitch.tv/helix/users?login={username}",
                headers={
                    'Client-ID': TWITCH_CLIENT_ID,
                    'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}'
                }
            )
            data = await response.json()
            return data['data'][0]['profile_image_url'] if data['data'] else ""
        except Exception as e:
            print(f"Error fetching profile image for {username}: {e}")
            return ""


@app.route('/api/streamers')
def get_streamers():
    """API endpoint to return all monitored streamers and their status."""
    users = TwitchUser.query.all()
    return jsonify([
        {
            'username': u.username,
            'is_live': u.is_live,
            'stream_title': u.stream_title,
            'game_name': u.game_name,
            'game_image_url': u.game_image_url,
            'profile_image_url': u.profile_image_url
        } for u in users
    ])

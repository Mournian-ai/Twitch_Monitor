from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, TwitchUser  # Import your database and model
from dotenv import load_dotenv
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
                    'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}',
                },
            )
            user_data = await response.json()
            if 'data' in user_data and user_data['data']:
                return user_data['data'][0]['profile_image_url']
            else:
                return None
        except Exception as e:
            print(f"Error fetching profile image for {username}: {e}")
            return None


async def fetch_game_name_and_image(game_id):
    """Fetch the game name and box art using the Twitch API."""
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.get(
                f"https://api.twitch.tv/helix/games?id={game_id}",
                headers={
                    'Client-ID': TWITCH_CLIENT_ID,
                    'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}',
                },
            )
            game_data = await response.json()
            if 'data' in game_data and game_data['data']:
                game_name = game_data['data'][0]['name']
                game_image = game_data['data'][0]['box_art_url'].replace("{width}x{height}", "40x40")
                return game_name, game_image
            else:
                return None, None
        except Exception as e:
            print(f"Error fetching game info for game_id {game_id}: {e}")
            return None, None


@app.route('/')
def index():
    """Render the main page."""
    users = TwitchUser.query.order_by(TwitchUser.is_live.desc()).all()  # Live users first
    return render_template('index.html', users=users)


@app.route('/add', methods=['POST'])
def add_streamer():
    """Add a new streamer to the database."""
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        flash("Incorrect password. Access denied.")
        return redirect(url_for('index'))

    username = request.form['username'].strip()

    # Check if the user already exists
    existing_user = TwitchUser.query.filter_by(username=username).first()
    if existing_user:
        flash(f"Streamer {username} already exists.")
        return redirect(url_for('index'))

    # Fetch the profile image asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    profile_image_url = loop.run_until_complete(fetch_profile_image(username))

    new_user = TwitchUser(username=username, profile_image_url=profile_image_url)
    db.session.add(new_user)
    db.session.commit()
    flash(f"Streamer {username} added successfully!")
    return redirect(url_for('index'))


@app.route('/remove/<int:user_id>', methods=['POST'])
def remove_streamer(user_id):
    """Remove a streamer from the database."""
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        flash("Incorrect password. Access denied.")
        return redirect(url_for('index'))

    user = TwitchUser.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f"Streamer {user.username} removed successfully!")
    else:
        flash("Streamer not found.")
    return redirect(url_for('index'))


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug=True, host='0.0.0.0', port=5000)

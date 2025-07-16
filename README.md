# Twitch Monitor

Twitch Monitor is a small Flask application for tracking a list of Twitch streamers and notifying a Discord channel when someone goes live. It provides a web UI to manage streamers, stores data with SQLAlchemy and periodically checks the Twitch API.

## Features

- **Flask web interface** to add or remove streamers.
- **Database** powered by `Flask-SQLAlchemy` to persist streamers and their live status.
- **Background monitor** that calls the Twitch API, updates the database, and can send Discord notifications when a streamer goes live.
- **Environment based configuration** using a `.env` file.

## Getting Started

### Clone the repository

```bash
git clone <repo-url>
cd Twitch_Monitor
```

### Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment configuration

Copy the example environment file and fill in your credentials:

```bash
cp Twitch_Monitor/env.example .env
```

Edit `.env` and set the variables such as `TWITCH_CLIENT_ID`, `TWITCH_ACCESS_TOKEN`, `DISCORD_WEBHOOK_URL` and other Twitch settings (`TWITCH_BOT_TOKEN`, `TWITCH_CHANNEL`, `TWITCH_NICK`, `TWITCH_PREFIX`, `TWITCH_CLIENT_SECRET`, `TWITCH_REFRESH_TOKEN`).

## Usage

Run the Flask application:

```bash
cd Twitch_Monitor
python server.py
```

In another terminal, start the monitor process:

```bash
python twitch_monitor.py
```

The web interface will be available at `http://localhost:5000` where you can manage the list of streamers.

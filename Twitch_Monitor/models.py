from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TwitchUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    is_live = db.Column(db.Boolean, default=False)
    profile_image_url = db.Column(db.String(300), default="")
    stream_title = db.Column(db.String(300), default="")
    game_name = db.Column(db.String(150), default="")
    game_image_url = db.Column(db.String(300), default="")  # New field for game image URL

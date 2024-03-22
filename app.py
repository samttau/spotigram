from flask import Flask, request, jsonify
import os
import telegram
from dotenv import load_dotenv
import sqlite3
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Get the playlist link from the environment variable
playlist_link = os.getenv("PLAYLIST_LINK", "")

# Initialise Flask app
app = Flask(__name__)

# Initialise Telegram bot
bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
chat_id = os.getenv("TELEGRAM_CHANNEL_ID")

# Database setup
db_file = os.getenv("DATABASE_FILE", "my_bot.db")
conn = sqlite3.connect(db_file)

def initialise_database():
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS songs (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       artist TEXT NOT NULL,
                       song_link TEXT NOT NULL
                   )''')
    conn.commit()

# Define a route to handle Spotify webhook notifications
@app.route('/webhook/spotify', methods=['POST'])
def spotify_webhook():
    data = request.json
    
    # Prepare the database to preserve a record of the existing songs outside of the spotify playlist
    initialise_database()

    # Process the incoming Spotify webhook event using Pandas
    added_tracks = data.get('added_tracks', [])
    df = pd.DataFrame(added_tracks)

    # Process new tracks
    for _, track in df.iterrows():
        name = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])
        song_link = track['external_urls']['spotify']

        message = f"New song added to the playlist:\nName: {name}\nArtist(s): {artists}\nLink: {song_link}\nPlaylist: {playlist_link}"
        # Post the message to the telegram channel
        send_message(message)

        # Insert the new song into the database
        cursor = conn.cursor()
        cursor.execute("INSERT INTO songs (name, artist, song_link) VALUES (?, ?, ?)", (name, artists, song_link))
        conn.commit()

    return jsonify({"success": True})

def send_message(message):
    bot.send_message(chat_id=chat_id, text=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
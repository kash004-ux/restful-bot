import os
import json
import random
import requests
import subprocess
import time
from datetime import datetime
from pathlib import Path
import googleapiclient.discovery
import googleapiclient.http
from google.oauth2.credentials import Credentials

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY")
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

CHANNEL = "RestfulTalesTunes"
OUTPUT_DIR = Path("/tmp/rtt_output")
OUTPUT_DIR.mkdir(exist_ok=True)

SOUNDS = [
    {"id": "rain", "label": "Gentle Rain", "desc": "soft rainfall on leaves"},
    {"id": "ocean", "label": "Ocean Waves", "desc": "calm ocean waves on shore"},
    {"id": "forest", "label": "Forest Night", "desc": "crickets and night insects"},
    {"id": "fireplace", "label": "Crackling Fireplace", "desc": "warm crackling fire​​​​​​​​​​​​​​​​


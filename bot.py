import os, json, random, requests, subprocess, time
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
    {"id": "rain", "label": "Gentle Rain", "desc": "soft rainfall"},
    {"id": "ocean", "label": "Ocean Waves", "desc": "calm waves"},
    {"id": "forest", "label": "Forest Night", "desc": "crickets"},
    {"id": "fireplace", "label": "Fireplace", "desc": "crackling fire"},
    {"id": "thunderstorm", "label": "Thunderstorm", "desc": "distant thunder"},
    {"id": "fan", "label": "Fan Noise", "desc": "gentle fan hum"},
    {"id": "cafe", "label": "Coffee Shop", "desc": "ambient cafe"},
    {"id": "whitenoise", "label": "White Noise", "desc": "pure white noise"},
]

STORIES = [
    {"id": "space", "label": "Space Adventure", "age": "3-5"},
    {"id": "forest", "label": "Enchanted Forest", "age": "3-5"},
    {"id": "ocean", "label": "Under the Sea", "age": "3-5"},
    {"id": "dragons", "label": "Friendly Dragons", "age": "4-6"},
    {"id": "farm", "label": "Farm Animals", "age": "2-4"},
    {"id": "princess", "label": "Royal Kingdom", "age": "4-6"},
    {"id": "dinosaurs", "label": "Dinosaur Land", "age": "3-5"},
    {"id": "clouds", "label": "Cloud Kingdom", "age": "3-5"},
]

VISUALS = {
    "rain": "dark rainy night, raindrops on window, moody blue, cinematic 4k",
    "ocean": "moonlit ocean at night, gentle waves, stars, peaceful cinematic",
    "forest": "dark forest at night, moonlight through trees, fireflies, misty 4k",
    "fireplace": "cozy fireplace glowing orange, warm living room, night, peaceful",
    "thunderstorm": "storm clouds, lightning in distance, rain on window, cinematic",
    "fan": "minimal dark room",
}

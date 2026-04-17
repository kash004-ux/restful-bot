import os, json, random, requests, subprocess, time, sys, traceback
from datetime import datetime
from pathlib import Path
import googleapiclient.discovery
import googleapiclient.http
from google.oauth2.credentials import Credentials

print("Nightfall Audio Co Bot starting...", flush=True)

# ── API Keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY     = os.environ.get("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY    = os.environ.get("ELEVENLABS_API_KEY")
PEXELS_API_KEY        = os.environ.get("PEXELS_API_KEY")
FREESOUND_CLIENT_ID   = os.environ.get("FREESOUND_CLIENT_ID")
FREESOUND_SECRET      = os.environ.get("FREESOUND_SECRET")
YOUTUBE_CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

CHANNEL    = "Nightfall Audio Co"
HANDLE     = "@NightfallAudioCo"
OUTPUT_DIR = Path("/tmp/nightfall_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Sound library ─────────────────────────────────────────────────────────────
# Single sounds
SINGLE_SOUNDS = [
    {"id": "rain",         "label": "Gentle Rain",        "freesound_ids": [584943, 399072], "pexels": "rain night window dark"},
    {"id": "ocean",        "label": "Ocean Waves",        "freesound_ids": [578524],         "pexels": "ocean waves night moonlight"},
    {"id": "forest",       "label": "Forest Night",       "freesound_ids": [405515],         "pexels": "forest night stars dark trees"},
    {"id": "fireplace",    "label": "Crackling Fireplace","freesound_ids": [729396, 729395], "pexels": "fireplace fire cozy dark night"},
    {"id": "thunderstorm", "label": "Thunderstorm",       "freesound_ids": [21042],          "pexels": "storm lightning dark clouds night"},
    {"id": "whitenoise",   "label": "White Noise",        "freesound_ids": [347576],         "pexels": "dark night sky stars minimal"},
    {"id": "softnoise",    "label": "Soft Ambient Noise", "freesound_ids": [403326],         "pexels": "misty forest fog night dark"},
]

# Combo sounds — two tracks layered together
COMBO_SOUNDS = [
    {
        "id": "fire_crickets",
        "label": "Campfire & Forest Crickets",
        "freesound_ids_a": [729396],
        "freesound_ids_b": [405515],
        "pexels": "campfire night stars forest moonlight",
    },
    {
        "id": "rain_fire",
        "label": "Rain & Crackling Fire",
        "freesound_ids_a": [584943],
        "freesound_ids_b": [729396],
        "pexels": "rainy night window fireplace cozy",
    },
    {
        "id": "ocean_rain",
        "label": "Ocean & Gentle Rain",
        "freesound_ids_a": [578524],
        "freesound_ids_b": [584943],
        "pexels": "stormy ocean beach night rain",
    },
    {
        "id": "thunder_forest",
        "label": "Thunderstorm & Forest",
        "freesound_ids_a": [21042],
        "freesound_ids_b": [405515],
        "pexels": "storm dark forest lightning night",
    },
    {
        "id": "rain_forest",
        "label": "Rain & Forest Night",
        "freesound_ids_a": [584943],
        "freesound_ids_b": [405515],
        "pexels": "rain forest night dark trees",
    },
]

VIDEO_DURATION_HOURS = 1  # Change to 8 after monetisation

# ── Freesound ─────────────────────────────────────────────────────────────────
def get_freesound_token():
    r = requests.post(
        "https://freesound.org/apiv2/oauth2/access_token/",
        data={
            "client_id": FREESOUND_CLIENT_ID,
            "client_secret": FREESOUND_SECRET,
            "grant_type": "client_credentials",
        }
    )
    r.raise_for_status()
    return r.json()["access_token"]

def download_freesound(sound_id, output_path, token):
    print(f"  Downloading sound {sound_id} from Freesound...", flush=True)
    r = requests.get(
        f"https://freesound.org/apiv2/sounds/{sound_id}/",
        headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    data = r.json()
    preview_url = data["previews"]["preview-hq-mp3"]
    audio_data = requests.get(preview_url, headers={"Authorization": f"Bearer {token}"}).content
    with open(output_path, "wb") as f:
        f.write(audio_data)
    print(f"  ✓ Sound saved: {output_path}", flush=True)

# ── Pexels ────────────────────────────────────────────────────────────────────
def fetch_pexels_image(query, output_path):
    print(f"  Fetching Pexels image for: {query}", flush=True)
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "per_page": 15, "orientation": "landscape"}
    )
    r.raise_for_status()
    photos = r.json().get("photos", [])
    if not photos:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": "night nature dark", "per_page": 15, "orientation": "landscape"}
        )
        photos = r.json().get("photos", [])
    photo = random.choice(photos)
    img_url = photo["src"]["original"]
    img_data = requests.get(img_url).content
    with open(output_path, "wb") as f:
        f.write(img_data)
    print(f"  ✓ Image saved: {output_path}", flush=True)

# ── FFmpeg Mix ────────────────────────────────────────────────────────────────
def mix_audio(audio_a, audio_b, output_path):
    print("  Mixing audio tracks...", flush=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(audio_a),
        "-i", str(audio_b),
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=2[aout]",
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-q:a", "2",
        str(output_path)
    ], check=True, capture_output=True)
    print(f"  ✓ Mixed audio: {output_path}", flush=True)

# ── FFmpeg Assemble ───────────────────────────────────────────────────────────
def make_video(img, audio, out, hours=1):
    print(f"  Assembling {hours}hr video...", flush=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img),
        "-stream_loop", "-1", "-i", str(audio),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(int(hours * 3600)),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-movflags", "+faststart",
        str(out)
    ], check=True)
    print(f"  ✓ Video ready: {out}", flush=True)

# ── Claude ────────────────────────────────────────────────────────────────────
def claude(prompt):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]

def generate_metadata(sound_label, is_combo=False):
    duration = f"{VIDEO_DURATION_HOURS} hour" if VIDEO_DURATION_HOURS == 1 else f"{VIDEO_DURATION_HOURS} hours"
    prompt = f"""You are a YouTube SEO expert for sleep and relaxation content.
Generate metadata for a {duration} "{sound_label}" sleep sound video for the channel {CHANNEL} ({HANDLE}).

Return ONLY valid JSON, no markdown:
{{"title":"{duration} {sound_label} | Sleep Sounds | {CHANNEL}","description":"3 paragraph YouTube description about this sleep sound, its benefits for relaxation and sleep, and a call to action to subscribe to {HANDLE} for daily sleep sounds","tags":["sleep sounds","relaxing sounds","sleep music","white noise","ambient sounds","{sound_label.lower()}","sleep aid","relaxation","meditation","study music","focus music","nightfall audio","sleep","insomnia relief","calm music"]}}"""
    raw = claude(prompt)
    return json.loads(raw.replace("```json","").replace("```","").strip())

# ── YouTube upload ────────────────────────────────────────────────────────────
def upload(path, title, description, tags):
    print(f"  Uploading: {title}", flush=True)
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )
    yt = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    media = googleapiclient.http.MediaFileUpload(
        str(path), mimetype="video/mp4", resumable=True, chunksize=10*1024*1024
    )
    req = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st:
            print(f"  Upload: {int(st.progress()*100)}%", flush=True)
    print(f"  ✓ Live: https://youtube.com/watch?v={res['id']}", flush=True)
    return res["id"]

# ── Main run ──────────────────────────────────────────────────────────────────
def run():
    today = datetime.now().strftime("%Y-%m-%d-%H%M")
    print(f"\nNightfall Audio Co Bot — {today}", flush=True)

    d = OUTPUT_DIR / today
    d.mkdir(exist_ok=True)

    print("Getting Freesound token...", flush=True)
    fs_token = get_freesound_token()

    is_combo = random.random() < 0.4
    print(f"Type: {'Combo' if is_combo else 'Single'} sound", flush=True)

    try:
        if is_combo:
            sound = random.choice(COMBO_SOUNDS)
            print(f"Sound: {sound['label']}", flush=True)

            audio_a = d / "audio_a.mp3"
            audio_b = d / "audio_b.mp3"
            download_freesound(random.choice(sound["freesound_ids_a"]), audio_a, fs_token)
            download_freesound(random.choice(sound["freesound_ids_b"]), audio_b, fs_token)

            mixed_audio = d / "audio_mixed.mp3"
            mix_audio(audio_a, audio_b, mixed_audio)

            img = d / "bg.jpg"
            fetch_pexels_image(sound["pexels"], img)

            print("Generating metadata...", flush=True)
            meta = generate_metadata(sound["label"], is_combo=True)

            vid = d / "final.mp4"
            make_video(img, mixed_audio, vid, hours=VIDEO_DURATION_HOURS)

        else:
            sound = random.choice(SINGLE_SOUNDS)
            print(f"Sound: {sound['label']}", flush=True)

            audio = d / "audio.mp3"
            download_freesound(random.choice(sound["freesound_ids"]), audio, fs_token)

            img = d / "bg.jpg"
            fetch_pexels_image(sound["pexels"], img)

            print("Generating metadata...", flush=True)
            meta = generate_metadata(sound["label"])

            vid = d / "final.mp4"
            make_video(img, audio, vid, hours=VIDEO_DURATION_HOURS)

        upload(vid, meta["title"], meta["description"], meta["tags"])

        for f in d.iterdir():
            f.unlink()
        d.rmdir()

        print("✓ All done!", flush=True)

    except Exception as e:
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run()

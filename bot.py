import os, json, random, requests, subprocess, time, sys, traceback
from datetime import datetime
from pathlib import Path
import googleapiclient.discovery
import googleapiclient.http
from google.oauth2.credentials import Credentials

print("Bot starting...", flush=True)

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
    "ocean": "moonlit ocean at night, gentle waves, stars, peaceful",
    "forest": "dark forest at night, moonlight, fireflies, misty 4k",
    "fireplace": "cozy fireplace glowing orange, warm room, night",
    "thunderstorm": "storm clouds, lightning, rain on window, cinematic",
    "fan": "minimal dark room, soft moonlight, calm 4k",
    "cafe": "cozy cafe at night, warm lights, rain outside",
    "whitenoise": "abstract dark waves, flowing light, minimal 4k",
    "space": "magical starry galaxy, glowing planets, soft purple nebula, dreamy cosmic landscape, no people",
    "forest_story": "magical glowing forest at night, fairy lights, fireflies, enchanted trees, soft mist, no people",
    "ocean_story": "magical underwater coral reef, glowing sea creatures, soft blue light, bubbles, no people",
    "dragons": "cozy cave with glowing crystals, soft candlelight, dragon eggs, magical treasure, no people",
    "farm": "peaceful moonlit farm, glowing barn, sleeping animals, stars, flowers, no people",
    "princess": "magical glowing castle at night, floating lanterns, moonlight, enchanted garden, no people",
    "dinosaurs": "lush moonlit jungle, glowing plants, ancient trees, fireflies, soft mist, no people",
    "clouds": "dreamy cloudscape at sunset, glowing clouds, rainbow colours, floating islands, no people",
}

VOICES = {
    "story": "21m00Tcm4TlvDq8ikWAM",
    "ambient": "AZnzlk1XvdvUeBnXmlld",
}
def claude(prompt):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]

def sound_meta(sound):
    raw = claude(f'YouTube SEO for @{CHANNEL}. Metadata for 8hr {sound["label"]} sleep sound. Return ONLY JSON: {{"title":"under 70 chars","description":"3 paragraphs","tags":["t1","t2","t3","t4","t5","t6","t7","t8","t9","t10"],"intro":"20 second calming intro starting with Welcome to RestfulTalesTunes"}}')
    return json.loads(raw.replace("```json","").replace("```","").strip())

def story_meta(theme):
    raw = claude(f'Bedtime story for @{CHANNEL}. Theme {theme["label"]} age {theme["age"]}. Return ONLY JSON: {{"title":"under 70 chars","story":"300 word bedtime story","description":"3 paragraphs","tags":["t1","t2","t3","t4","t5","t6","t7","t8","t9","t10"]}}')
    return json.loads(raw.replace("```json","").replace("```","").strip())

def tts(text, voice_id, path):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_monolingual_v1", "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}}
    )
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"Audio done: {path}", flush=True)

def image(prompt, path):
    r = requests.post(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        headers={"authorization": f"Bearer {LEONARDO_API_KEY}", "content-type": "application/json"},
                json={
            "prompt": prompt,
            "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
            "width": 1024,
            "height": 768,
            "num_images": 1,
            "public": False
        }
    )
    r.raise_for_status()
    gid = r.json()["sdGenerationJob"]["generationId"]
    print(f"Image generating...", flush=True)
    for _ in range(30):
        time.sleep(5)
        d = requests.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{gid}", headers={"authorization": f"Bearer {LEONARDO_API_KEY}"}).json().get("generations_by_pk", {})
        if d.get("status") == "COMPLETE":
            with open(path, "wb") as f:
                f.write(requests.get(d["generated_images"][0]["url"]).content)
            print(f"Image done: {path}", flush=True)
            return
    raise Exception("Image timed out")

def make_video(img, audio, out, hours=0.2):
    print("Making video...", flush=True)
    subprocess.run(["ffmpeg","-y","-loop","1","-i",str(img),"-stream_loop","-1","-i",str(audio),"-c:v","libx264","-tune","stillimage","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p","-t",str(hours*3600),"-vf","scale=1920:1080","-movflags","+faststart",str(out)], check=True)
    print(f"Video done: {out}", flush=True)

def make_story_video(img, audio, out):
    print("Making story video...", flush=True)
    subprocess.run(["ffmpeg","-y","-loop","1","-i",str(img),"-i",str(audio),"-c:v","libx264","-tune","stillimage","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p","-vf","scale=1920:1080","-movflags","+faststart","-shortest",str(out)], check=True)
    print(f"Story video done: {out}", flush=True)

def make_short(audio_path, img_path, out_path):
    print("Making Short...", flush=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", "58",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
        "-movflags", "+faststart",
        "-shortest",
        str(out_path)
    ], check=True)
    print(f"Short done: {out_path}", flush=True)

def upload_short(path, title, description, tags):
    print(f"Uploading Short: {title}", flush=True)
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
            "title": title,
            "description": description,
            "tags": tags + ["shorts", "youtubeshorts"],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }
    media = googleapiclient.http.MediaFileUpload(
        str(path), 
        mimetype="video/mp4", 
        resumable=True, 
        chunksize=10*1024*1024
    )
    req = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st:
            print(f"Short upload: {int(st.progress()*100)}%", flush=True)
    print(f"Short live: https://youtube.com/shorts/{res['id']}", flush=True)
    return res["id"]

def upload(path, title, desc, tags):
    print(f"Uploading: {title}", flush=True)
    creds = Credentials(token=None, refresh_token=YOUTUBE_REFRESH_TOKEN, client_id=YOUTUBE_CLIENT_ID, client_secret=YOUTUBE_CLIENT_SECRET, token_uri="https://oauth2.googleapis.com/token")
    yt = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    media = googleapiclient.http.MediaFileUpload(str(path), mimetype="video/mp4", resumable=True, chunksize=10*1024*1024)
    req = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st:
            print(f"Upload: {int(st.progress()*100)}%", flush=True)
    print(f"Live: https://youtube.com/watch?v={res['id']}", flush=True)
    return res["id"]

def run():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"RestfulTalesTunes Bot - {today}", flush=True)
    ctype = random.choice(["sleep_sound", "bedtime_story"])
    print(f"Type: {ctype}", flush=True)
    d = OUTPUT_DIR / today
    d.mkdir(exist_ok=True)
    try:
        if ctype == "sleep_sound":
            s = random.choice(SOUNDS)
            print(f"Sound: {s['label']}", flush=True)
            meta = sound_meta(s)
            audio = d / "audio.mp3"
            tts(meta["intro"], VOICES["ambient"], audio)
            img = d / "bg.jpg"
            image(VISUALS.get(s["id"], VISUALS["forest"]), img)
            vid = d / "final.mp4"
            make_video(img, audio, vid)
            upload(vid, meta["title"], meta["description"], meta["tags"])
            short_path = d / "short.mp4"
            make_short(audio, img, short_path)
            upload_short(short_path, meta["title"][:85] + " #Shorts", meta["description"], meta["tags"]) 
        else:
            t = random.choice(STORIES)
            print(f"Theme: {t['label']}", flush=True)
            meta = story_meta(t)
            audio = d / "audio.mp3"
            tts(meta["story"], VOICES["story"], audio)
            img = d / "bg.jpg"
            vkey = t["id"] + "_story" if t["id"] + "_story" in VISUALS else t["id"]
            image(VISUALS.get(vkey, VISUALS["clouds"]), img)
            vid = d / "final.mp4"
            make_story_video(img, audio, vid)
            upload(vid, meta["title"], meta["description"], meta["tags"])
            short_path = d / "short.mp4"
            make_short(audio, img, short_path)
            upload_short(short_path, meta["title"][:85] + " #Shorts", meta["description"], meta["tags"]) 
        for f in d.iterdir():
            f.unlink()
        print("All done!", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run()

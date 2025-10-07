import subprocess
import math
import random
import os
import requests
from zipfile import ZipFile
import json
import time
import logging
import base64
import uuid
import secrets


logging.basicConfig(
    level=logging.INFO, # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load params
with open("params/render.json") as f:
    params = json.load(f)


def get_ip():
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        data = r.json()
        r = f"{data.get('query','')} | {data.get('country','')} | {data.get('city','')}"
        logging.info(f'location: {f}')

        return r
    except Exception as e:
        logging.info(f'location: unknown')
        return None


logging.info(json.dumps(params, indent=4, ensure_ascii=False))


def dur(f):
    logging.debug(f"Getting duration of {f}")
    out = subprocess.check_output((
        f'ffprobe -v error -show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 "{f}"'
    ), shell=True)
    duration = float(out.strip())
    logging.debug(f"Duration: {duration}")
    return duration


def concat_video(vs: list[str], secs: float, dir: str, shuffle=True):
    logging.info(f"Concatenating {len(vs)} videos into {dir}/concat.mp4 for {secs} seconds")
    if shuffle:
        random.shuffle(vs)

    vdur = sum(dur(v) for v in vs)
    logging.info(f"Total video duration: {vdur}")
    rep = math.ceil(secs / vdur)
    logging.info(f"Repeating videos {rep} times to reach target duration")
    vs = vs * rep

    output = f"{dir}/concat.mp4"
    videos_path = f"{dir}/videos.txt"

    with open(videos_path, "w") as f:
        f.write("\n".join([f"file '{v}'" for v in vs]))

    tmp_concat = f"{dir}/tmp_concat.mp4"

    logging.info(f"Running ffmpeg concat")
    subprocess.run((
        f'ffmpeg -y -v error -f concat -safe 0 -i "{videos_path}" -c copy "{tmp_concat}"'
    ), shell=True, check=True)

    logging.info(f"Trimming video to {secs} seconds")
    subprocess.run((
        f'ffmpeg -y -v error -i "{tmp_concat}" -t {secs:.3f} -c copy "{output}"'
    ), shell=True, check=True)

    logging.info(f"Video concatenation done: {output}")
    return output


def concat_audio(video_file, audio_file, sub_file, output):
    logging.info(f"Merging video {video_file} with audio {audio_file} and subtitles {sub_file}")
    subprocess.run((
        f'ffmpeg -y -v error -i "{video_file}" -i "{audio_file}" '
        f'-vf "ass={sub_file}" '
        f'-map 0:v:0 -map 1:a:0 -c:v libx264 -preset veryfast -crf 23 -c:a copy "{output}"'
    ), check=True, shell=True)
    logging.info(f"Audio concatenation done: {output}")


def upload_s3(filepath):
    key = secrets.token_urlsafe(8)[:10] + '.mp4'
    api = f'https://g86.xyz/api/upload?k={key}'
    r = requests.get(api)
    r.raise_for_status()
    upload_url = r.text.strip()

    with open(filepath, "rb") as f:
        put = requests.put(upload_url, data=f)
        put.raise_for_status()

    return f"https://minhvh-sss.hf.space/tmp/{key}"


def load_params():
    clips_url = params.get("clips")

    logging.info(f"download < {clips_url}")
    r = requests.get(clips_url)
    r.raise_for_status()
    with open("clips.zip", "wb") as f:
        f.write(r.content)

    with ZipFile("clips.zip", "r") as zip_ref:
        zip_ref.extractall("clips")
    logging.info("Clips extracted")

    # Download audio and subtitles
    for url, out in [(params.get("subs"), "sub.txt"), (params.get("audio"), "audio.mp3")]:
        logging.info(f"download < {url}")
        r = requests.get(url)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
        logging.info(f"{out} downloaded")

def base64_encode(text):
    return base64.b64encode(text.encode()).decode()

def notify(data):
    payload = {"status": "success", "data": data}
    requests.post(params.get('webhook'), json=payload)
    
    logging.info("Notification sent")


def run():
    get_ip()
    load_params()

    start = time.time()
    audio_file = 'audio.mp3'
    sub_file = 'sub.txt'
    dir = 'clips'

    files = [f"{dir}/{e}" for e in os.listdir(dir) if e.lower().endswith(".mp4")]
    logging.info(f"Video files: {files}")

    concat_file = concat_video(files, dur(audio_file), '.')
    concat_audio(concat_file, audio_file, sub_file, 'final.mp4')
    path = upload_s3('final.mp4')
    logging.info(f'output: {path}') 

    logging.info(f"Total time: {time.time() - start:.2f}s")
    notify(path)
    


if __name__ == '__main__':
    run()
    

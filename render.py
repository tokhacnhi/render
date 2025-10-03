import subprocess
import math
import random
import os

def dur(f):
    out = subprocess.check_output((
        f'ffprobe -v error -show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 "{f}"'
    ), shell=True)
    return float(out.strip())


def concat_video(vs: list[str], secs: float, dir: str, shuffle=True):
    if shuffle:
        random.shuffle(vs)

    vdur = sum(dur(v) for v in vs)
    rep = math.ceil(secs / vdur)
    vs = vs * rep
    output = f"{dir}/concat.mp4"
    videos_path = f"{dir}/videos.txt"

    with open(videos_path, "w") as f:
        f.write("\n".join([f"file '{v}'" for v in vs]))

    tmp_concat = f"{dir}/tmp_concat.mp4"

    subprocess.run((
        f'ffmpeg -y -v error -f concat -safe 0 -i "{videos_path}" -c copy "{tmp_concat}"'
    ), shell=True, check=True)

    subprocess.run((
        f'ffmpeg -y -v error -i "{tmp_concat}" -t {secs:.3f} -c copy "{output}"'
    ), shell=True, check=True)

    return output

def concat_audio(video_file, audio_file, sub_file, output):
    subprocess.run((
        f'ffmpeg -y -i "{video_file}" -i "{audio_file}" '
        f'-vf "ass={sub_file}" '
        f'-map 0:v:0 -map 1:a:0 -c:v libx264 -preset veryfast -crf 23 -c:a copy "{output}"'
    ), check=True, shell=True)


def upload_s3(name, filepath):
    dm = 'https://minhvh-tool.hf.space/gradio_api'
    files = {
        "files": (name, open(file, "rb"))
    }
    response = requests.post(f'{dm}/upload', files=files)
    
    return f'{dm}/file={response.text}'

def run(webhook):
    audio_file = 'audio.mp3'
    sub_file = 'sub.txt'
    dir = 'clips'

    files = [f"{dir}/{e}" for e in os.listdir(dir) if e.lower().endswith(".mp4")]


    with open(audio_file, "wb") as f:
        f.write(requests.get(audio_url).content)

    with open(sub_file, "wb") as f:
        f.write(requests.get(sub_url).content)

    concat_file = concat_video(files, dur(audio_file), '/tmp')

    concat_audio(concat_file, audio_file, sub_file, 'final.mp4')

    return upload_s3('final.mp4')

    


if __name__ == '__main__':
  fire.Fire(run)
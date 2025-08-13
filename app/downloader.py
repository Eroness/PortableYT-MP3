import os
import sys
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode


def get_ffmpeg_paths():
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # folder tymczasowy exe
    else:
        base_path = os.path.abspath(".")

    ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
    ffprobe_path = os.path.join(base_path, "ffprobe.exe")
    return ffmpeg_path, ffprobe_path


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def download_audio(url, output_folder, output_name=None):
    print(
        f"Starting download: url={url}, output_folder={output_folder}, output_name={output_name}"
    )
    outtmpl = (
        os.path.join(output_folder, f"{output_name}.%(ext)s")
        if output_name
        else os.path.join(output_folder, "%(title)s.%(ext)s")
    )

    ffmpeg_path, ffprobe_path = get_ffmpeg_paths()

    ydl_opts = {
        "ffmpeg_location": ffmpeg_path,
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # The final downloaded file path (full path)
    file_path = info["requested_downloads"][0]["filepath"]
    print(f"Download finished: {file_path}")

    # If you want just the file name without folder path:
    file_name = os.path.basename(file_path)
    return file_name


def clean_youtube_url(url: str) -> str:
    # Normalize URL (add https if missing)
    if not url.startswith("http"):
        url = "https://" + url

    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Keep only the 'v' param if it exists
    clean_params = {}
    if "v" in query_params:
        clean_params["v"] = query_params["v"]

    # Rebuild query string
    clean_query = urlencode(clean_params, doseq=True)

    # Rebuild the URL without extra params
    clean_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            clean_query,
            parsed_url.fragment,
        )
    )

    return clean_url

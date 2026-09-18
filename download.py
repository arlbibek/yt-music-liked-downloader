#!/usr/bin/env python3
"""
Download all tracks from one or more YouTube Music playlists as audio files,
using multiple threads for concurrency. Configuration is read from a YAML file.

Requires:
    pip install -r requirements.txt
    Node.js installed and on PATH
    ffmpeg installed and on PATH
    A cookies.txt file (Netscape format) exported from your browser
"""

import argparse
import os
import sys
import yaml
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    "output_dir": ".",
    "cookies": "./cookies.txt",
    "audio_format": "mp3",
    "audio_quality": "192",
    "player_client": "tv",
    "max_workers": 4,
}


def load_config(path):
    if not os.path.isfile(path):
        print(f"Config file not found: {path}", file=sys.stderr)
        print("Copy config.example.yaml to config.yaml and edit it first.", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    config = {**DEFAULTS, **raw}
    if "playlists" not in config or not config["playlists"]:
        print("Config must include at least one entry under 'playlists'.", file=sys.stderr)
        sys.exit(1)
    return config


def build_opts(output_dir, cookies, audio_format, audio_quality, player_client, archive_path):
    return {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s - %(artist,creator,uploader)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": audio_quality,
        }],
        "cookiefile": cookies,
        "js_runtimes": {"node": {}},
        "extractor_args": {"youtube": {"player_client": [player_client], "player_skip": ["webpage"]}},
        "ignoreerrors": True,
        "download_archive": archive_path,
        "quiet": True,
        "no_warnings": True,
    }


def get_video_entries(playlist_url, opts, playlist_name):
    list_opts = {**opts, "extract_flat": True, "quiet": True}
    with yt_dlp.YoutubeDL(list_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    if info is None:
        print(f"Could not read playlist '{playlist_name}' ({playlist_url}).", file=sys.stderr)
        print("Likely causes: expired/invalid cookies, the playlist is private and", file=sys.stderr)
        print("not accessible with the current account, or the URL/ID is wrong.", file=sys.stderr)
        return []

    entries = info.get("entries")
    if not entries:
        print(f"Playlist '{playlist_name}' returned no entries (empty or inaccessible).", file=sys.stderr)
        return []

    return [(entry["id"], entry.get("title", entry["id"])) for entry in entries if entry]


def download_one(video_id, title, opts):
    url = f"https://music.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return (video_id, title, "ok")
    except Exception as e:
        return (video_id, title, f"failed: {e}")


def run_playlist(playlist, config):
    name = playlist.get("name", playlist["url"])
    url = playlist["url"]
    output_dir = playlist.get("output_dir", config["output_dir"])
    max_workers = playlist.get("max_workers", config["max_workers"])

    os.makedirs(output_dir, exist_ok=True)

    archive_dir = os.path.join(PROJECT_DIR, "archives")
    os.makedirs(archive_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()
    archive_path = os.path.join(archive_dir, f"{safe_name}.txt")

    opts = build_opts(
        output_dir=output_dir,
        cookies=config["cookies"],
        audio_format=config["audio_format"],
        audio_quality=config["audio_quality"],
        player_client=config["player_client"],
        archive_path=archive_path,
    )

    print(f"\n=== {name} ===")
    entries = get_video_entries(url, opts, name)
    if not entries:
        print(f"Skipping '{name}' — no tracks to download.")
        return

    print(f"Found {len(entries)} tracks. Downloading with {max_workers} threads into {output_dir}...")

    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {executor.submit(download_one, vid, title, opts): vid for vid, title in entries}

    completed = 0
    failed = 0
    try:
        for future in as_completed(futures):
            video_id, title, status = future.result()
            print(f"{title} [{video_id}]: {status}")
            if status == "ok":
                completed += 1
            else:
                failed += 1
    except KeyboardInterrupt:
        print("\nInterrupted. Cancelling pending downloads for this playlist...")
        executor.shutdown(wait=False, cancel_futures=True)
        print(f"Stopped. Completed: {completed}, Failed: {failed}, "
              f"Not started/interrupted: {len(futures) - completed - failed}")
        raise
    else:
        executor.shutdown(wait=True)
        print(f"Done with '{name}'. Completed: {completed}, Failed: {failed}")


def parse_args():
    p = argparse.ArgumentParser(description="Bulk-download YouTube Music playlists as audio, via config.yaml.")
    p.add_argument("--config", default="config.yaml", help="Path to config YAML file. Default: config.yaml")
    p.add_argument("--only", help="Only process the playlist with this exact 'name' from the config.")
    return p.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)

    if not os.path.isfile(config["cookies"]):
        print(f"Cookie file not found: {config['cookies']}", file=sys.stderr)
        print("Export cookies.txt (Netscape format) from your browser first.", file=sys.stderr)
        sys.exit(1)

    playlists = config["playlists"]
    if args.only:
        playlists = [p for p in playlists if p.get("name") == args.only]
        if not playlists:
            print(f"No playlist named '{args.only}' found in config.", file=sys.stderr)
            sys.exit(1)

    try:
        for playlist in playlists:
            run_playlist(playlist, config)
    except KeyboardInterrupt:
        print("\nInterrupted. Skipping remaining playlists.")
        sys.exit(1)


if __name__ == "__main__":
    main()
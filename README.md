# YT Music Liked Songs Downloader

Bulk-downloads a YouTube Music playlist (default: your Liked Songs) as audio files, using yt-dlp with multi-threaded downloads.

## Requirements

- Python 3.9+
- [Node.js](https://nodejs.org/) (LTS) — on PATH
- [ffmpeg](https://ffmpeg.org/) — on PATH
- A browser cookie export

## Setup

```bash
git clone https://github.com/yourusername/yt-music-liked-downloader.git
cd yt-music-liked-downloader
pip install -r requirements.txt
```

### Exporting cookies

YouTube Music's Liked Songs playlist requires an authenticated session. Export cookies in Netscape format:

1. Install a cookie-export browser extension (e.g. "Get cookies.txt LOCALLY").
2. Log into `music.youtube.com`.
3. Export cookies for `youtube.com` to a file named `cookies.txt` in this repo's root.

Cookies rotate periodically as a YouTube security measure — if downloads suddenly fail with a "cookies no longer valid" error, re-export.

## Configuration

Copy the example config and edit it:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
output_dir: ./music
cookies: ./cookies.txt
audio_format: mp3
audio_quality: "192"
player_client: tv
max_workers: 4

playlists:
  - name: Liked Songs
    url: https://music.youtube.com/playlist?list=LM

  - name: Some Public Playlist
    url: https://music.youtube.com/playlist?list=PUBLIC_ID
    output_dir: ./music/public-playlist # optional override
```

Each playlist entry needs `name` and `url`. `output_dir` and `max_workers` can optionally be overridden per playlist; anything else (cookies, audio format/quality, player client) applies globally to all playlists in the config.

## Usage

Run all configured playlists:

```bash
python download.py
```

Run just one:

```bash
python download.py --only "Liked Songs"
```

Use a different config file:

```bash
python download.py --config other-config.yaml
```

### Example

```bash
python download.py --output-dir ./music --audio-format flac --max-workers 3
```

## Why `--player-client tv`?

YouTube increasingly requires a Proof-of-Origin (PO) Token for most extraction clients (`web`, `web_music`, `mweb`). The `tv` client currently works with account cookies without a PO Token, at the cost of lower available audio bitrate (progressive format 18, ~96kbps). `web_safari` is worth testing if you want higher-bitrate audio-only streams — check with:

```bash
python -m yt_dlp --extractor-args "youtube:player_client=web_safari" --cookies cookies.txt -F <video-url>
```

This is an active cat-and-mouse situation between yt-dlp and YouTube. If downloads suddenly break, check the [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) for the current recommended client.

## Resuming interrupted runs

Downloads are tracked in `downloaded.txt` in the output directory. Rerunning the script skips anything already downloaded. `Ctrl+C` stops queuing new downloads but lets in-flight ones finish.

## A note on legality

Downloading audio from YouTube/YouTube Music violates their Terms of Service, and depending on the content, may infringe copyright. This tool is provided for personal, non-commercial use with content you have the right to download (e.g. your own uploads, Creative Commons–licensed tracks). You are responsible for how you use it.

## License

MIT — see LICENSE.

---

Made with ❤️ by [Bibek Aryal](https://bibeka.com.np).

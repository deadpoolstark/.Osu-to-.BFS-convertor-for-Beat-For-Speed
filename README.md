# 🏍️ BFS AI Chart Generator

A desktop tool that turns any YouTube song into a playable **Beat For Speed (.bfs)** chart. Paste a link, pick an engine, hit generate.

## Features

- 🎵 **YouTube → chart, end to end.** Downloads and extracts audio automatically via `yt-dlp`.
- 🖼️ **Optional cover art.** Drop in an image and it gets bundled into the `.bfs` package.
- ⚙️ **Two generation engines:**
  - **Lightweight (default)** — fast, local beat/onset detection via `librosa`. No GPU required.
  - **Heavy AI** — uses [Mapperatorinator](#credits) to generate a real AI-charted map. Slower, but much higher quality patterning. Runs in its own isolated Python 3.10 environment (managed automatically via `uv`), so it won't conflict with whatever Python version you already have installed.
- 🎚️ **Adjustable difficulty** — a slider sets the target star rating (1–10) when using Heavy AI.
- 🧠 **Smart obstacle placement** — automatically drops extra obstacles into dense/intense sections of the song, while guaranteeing they never overlap or crowd an actual note.
- 🚫 **No stacked columns** — a final safety pass guarantees only one note or obstacle ever occupies a given beat/lane, so nothing generated is physically un-hittable.
- 🎨 **Automatic theming** — cycles through a few built-in visual themes across the length of the track.

## Requirements

- Windows (tested) with Python 3.x installed
- [Git](https://git-scm.com/) (only required if you use the Heavy AI engine — used to clone Mapperatorinator)
- A decent internet connection for the first Heavy AI run (it downloads an isolated Python 3.10 runtime, PyTorch, and the Mapperatorinator model dependencies)

## Installation

```bash
git clone https://github.com/deadpoolstark/Better-.BFS-Generator-for-Beat-For-Speed
cd bfs-ai-chart-generator
pip install -r requirements.txt
python app.py
```

## Usage

1. Paste a YouTube URL.
2. (Optional) select a cover image.
3. Check **"Use Heavy AI"** if you want AI-generated charts instead of the fast local fallback, and drag the difficulty slider to taste(2 is the best).
4. Hit **Generate Chart**.
5. Your finished `.bfs` file lands in the `bfs/` folder, named after the song title.

Run with `python app.py --debug` if you want to watch what's happening under the hood (dependency installs, Mapperatorinator's own output, etc.) instead of a quiet GUI-only view.

### First-time Heavy AI setup

The first time you generate with Heavy AI checked, the app will automatically:
1. Install [`uv`](https://github.com/astral-sh/uv) into your Python environment.
2. Use `uv` to download a real, isolated Python 3.10 build and create a dedicated virtual environment for it (`mapperator_venv/`) — no admin rights needed.
3. Clone the Mapperatorinator repo.
4. Install PyTorch (CPU build) and the rest of Mapperatorinator's dependencies into that isolated environment.

This only happens once. Every generation after that reuses the same environment.

## Credits

Heavy AI chart generation is powered by **[Mapperatorinator](https://github.com/OliBomby/Mapperatorinator)** by **[OliBomby](https://github.com/OliBomby)** — all due respect to the actual mapping model doing the heavy lifting here. This project just wraps it with a GUI, a YouTube pipeline, and a converter into the `.bfs` format. Go check out the original repo and give it a star.

Lightweight fallback generation uses [`librosa`](https://librosa.org/) for beat tracking and onset detection.

Audio downloading via [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

## Disclaimer

This is an unofficial fan-made tool, not affiliated with the developers of Beat For Speed. Use responsibly and only with audio you have the right to use.

## License

No license provided. All rights reserved by default, if you want others to be able to fork, modify, or redistribute this freely, add a LICENSE file.

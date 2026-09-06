# 🏍️ Beat For Speed AI Chart Generator

A local Python tool that automatically generates fully playable `.bfs` charts for **Beat For Speed** directly from a YouTube URL. 

It uses the state-of-the-art **Mapperatorinator** AI to generate professional-level `.osu` maps, then converts them into Beat For Speed charts with smart obstacles and dynamic themes.

## ✨ Features
- 🧠 **Heavyweight AI:** Uses the 219M parameter Mapperatorinator Transformer model for human-like note placement.
- 📥 **YouTube Integration:** Automatically downloads and extracts audio.
- 🎯 **Smart Obstacles:** Automatically detects the 15 most intense "burst" sections and places `spawn_sting` obstacles.
-  **Dynamic Themes:** Injects city theme transitions (Cold Night ➔ Blue ➔ Red ➔ Gold).
- 🖼️ **Custom Cover Art:** Upload any JPG/PNG/WEBP image.
- 💾 **Organized Output:** Saves charts into a local `/bfs` folder, named after the actual song title.

## ⚠️ Prerequisites & Hardware Requirements
Because this uses a massive AI model, your PC needs to meet these requirements:
1. **Python 3.10** (Make sure to check **"Add Python to PATH"** during installation).
2. **Git** (Required to download the AI model).
3. **FFmpeg** (Required for YouTube audio extraction).
   - Windows: Run `winget install Gyan.FFmpeg` in Command Prompt.
4. **Hardware:** An **NVIDIA GPU** is highly recommended. It *will* run on CPU, but it may take 5-10 minutes per song instead of 30 seconds.

##  Installation & Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/deadpoolstark3/BFS-Generator.git
   cd BFS-Generator```
2. **Install the base requirements:**
    ```bash
    pip install -r requirements.txt```

## 🛠️ Troubleshooting & Support

  🐛 **Raise an Issue:**
    Open a new Issue on this GitHub repository.
  💬 **Discord**: Message me directly at deadpoolstark3

## ⏯️How to run:
 ▶️**run the following commands (based on what you want):**
   ```bash
python app-V-Mapperatorinator.py
``` 
for running it on Mapperatorinator(Osu->bsr conversion+1st run takes a while)
   **or**
   ```bash
   python app-V-Librosa
   ```
   quick and dirty but quite accurate.
## 🤝 Credits & Acknowledgements
    
  **Mapperatorinator by OliBomby**: The incredible AI osu! beatmap generator that powers this tool.
  **yt-dlp**: For YouTube downloading.
  **CustomTkinter**: For the beautiful UI.
  **Pillow (PIL)**: For image processing.

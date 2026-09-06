import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
import json
import zipfile
import shutil
import random
import yt_dlp
import librosa
import numpy as np
from PIL import Image

# --- APP SETTINGS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

def sanitize_filename(name):
    """Removes characters that Windows doesn't allow in file names."""
    clean = "".join(c for c in name if c not in r'\/:*?"<>|').strip()
    return clean if clean else "generated_chart"

class BFSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Beat For Speed AI Chart Generator")
        self.geometry("700x600")
        self.resizable(False, False)

        # Main Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self, text="🏍️ BFS AI Chart Generator", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(30, 10), padx=20)

        # YouTube URL Input
        self.url_label = ctk.CTkLabel(self, text="YouTube URL:", anchor="w")
        self.url_label.grid(row=1, column=0, pady=(10, 0), padx=40, sticky="w")

        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://www.youtube.com/watch?v=...", width=620)
        self.url_entry.grid(row=2, column=0, pady=10, padx=40)

        # Cover Image Input
        self.cover_label = ctk.CTkLabel(self, text="Cover Image (Optional):", anchor="w")
        self.cover_label.grid(row=3, column=0, pady=(10, 0), padx=40, sticky="w")

        self.cover_btn = ctk.CTkButton(self, text="Select Image", command=self.select_cover, width=150)
        self.cover_btn.grid(row=3, column=0, pady=10, padx=40, sticky="e")
        self.cover_path = ""

        # Generate Button
        self.generate_btn = ctk.CTkButton(self, text="🚀 Generate Chart", command=self.start_generation, font=ctk.CTkFont(size=16, weight="bold"), height=50)
        self.generate_btn.grid(row=4, column=0, pady=30, padx=40)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=620)
        self.progress_bar.grid(row=5, column=0, pady=10, padx=40)
        self.progress_bar.set(0)

        # Status Log
        self.status_label = ctk.CTkLabel(self, text="Ready to generate.", text_color="gray")
        self.status_label.grid(row=6, column=0, pady=(0, 30), padx=40)

    def select_cover(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.webp")])
        if filepath:
            self.cover_path = filepath
            self.cover_btn.configure(text=os.path.basename(filepath), fg_color="green")

    def start_generation(self):
        url = self.url_entry.get()
        if not url:
            self.update_status("Please enter a YouTube URL!", "red")
            return

        self.generate_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)

        # Run in background thread so UI doesn't freeze
        thread = threading.Thread(target=self.run_pipeline, args=(url,))
        thread.start()

    def run_pipeline(self, url):
        temp_dir = "temp_app_data"
        os.makedirs(temp_dir, exist_ok=True)

        # Create the 'bfs' folder to store the final files
        os.makedirs("bfs", exist_ok=True)

        try:
            # 1. Download + Grab the Song Title
            self.update_status("1/4: Downloading audio from YouTube...", "#00d4ff")
            self.progress_bar.set(0.1)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{temp_dir}/audio.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                raw_title = info.get('title', 'Unknown Title')
                uploader = info.get('uploader', 'Unknown Artist')

            # Clean the title so it's safe for Windows file names
            song_title = sanitize_filename(raw_title)

            audio_path = next((f for f in os.listdir(temp_dir) if f.endswith('.mp3')), None)
            if not audio_path: raise Exception("Audio download failed.")
            audio_path = os.path.join(temp_dir, audio_path)

            # 2. AI Generation (Lightweight Librosa)
            self.update_status("2/4: Analyzing audio & generating AI notes...", "#00d4ff")
            self.progress_bar.set(0.4)

            y, sr = librosa.load(audio_path, sr=22050)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(np.array(tempo).flatten()[0])
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            onset_beats = (onset_times / 60.0) * bpm

            # 3. Build Chart, Obstacles & Themes
            self.update_status("3/4: Adding smart obstacles & themes...", "#00d4ff")
            self.progress_bar.set(0.7)

            entities = [{"beat": 0.0, "key": 5, "datamodel": "custom_song_structure_gameplay/g00_s00_intro", "width": 0.25, "volume": 100}]
            for beat in onset_beats:
                humanized_beat = round(float(beat) + np.random.uniform(-0.02, 0.02), 4)
                chosen_key = int(np.random.choice([5, 6, 7, 8, 9]))
                entities.append({"beat": humanized_beat, "key": chosen_key, "datamodel": "custom_custom_spawn_cube/spawn_cube", "width": 0.25, "volume": 100})

            # Add 15 smart obstacles
            time_gaps = [onset_beats[i] - onset_beats[i-1] for i in range(1, len(onset_beats))]
            avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 1
            intense = [{"beat": onset_beats[i], "intensity": avg_gap / (onset_beats[i] - onset_beats[i-1])} for i in range(1, len(onset_beats)) if (onset_beats[i] - onset_beats[i-1]) < (avg_gap * 0.7)]
            intense.sort(key=lambda x: x["intensity"], reverse=True)
            for moment in intense[:15]:
                entities.append({"beat": round(moment["beat"], 4), "key": random.randint(5, 9), "datamodel": "custom_custom_spawn_cube/spawn_sting", "width": 0.25, "volume": 100})

            # Add City Themes & End Marker
            last_beat = max(onset_beats) if len(onset_beats) > 0 else 100
            entities.append({"beat": 0.0, "key": 1, "datamodel": "custom_themes/city_cold_night_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat * 0.25, 4), "key": 1, "datamodel": "custom_themes/city_blue_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat * 0.60, 4), "key": 1, "datamodel": "custom_themes/city_red_night_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat * 0.85, 4), "key": 1, "datamodel": "custom_themes/city_gold_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat, 4), "key": 5, "datamodel": "custom_song_structure_gameplay/end", "width": 0.25, "volume": 100})
            entities.sort(key=lambda x: x["beat"])

            final_chart = {
                "musicData": {"filename": "", "bpm": round(bpm, 2), "runBeats": 0.0},
                "entities": entities,
                "editorMeta": {"axisMap": [1,0,0,0,0,0,0,0,0,0], "datamodelTypes": [], "songStructure": {"version": "v2", "mode": "gameplay_compact", "source": "Local_App"}},
                "bfsMetadata": {
                    "songName": raw_title,          # Real title shows up in-game!
                    "artist": uploader,             # YouTube channel name as artist
                    "author": "Local AI Generator",
                    "difficulty": "Medium",
                    "genre": "AI",
                    "description": f"Generated from {url}",
                    "coverFileName": "cover.webp"
                }
            }

            # 4. Package and Save with the Song Title
            self.update_status("4/4: Packaging .bfs file...", "#00d4ff")
            self.progress_bar.set(0.9)

            output_bfs = os.path.join("bfs", f"{song_title}.bfs")

            with zipfile.ZipFile(output_bfs, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("chart.json", json.dumps(final_chart, indent=2))
                zf.write(audio_path, arcname="audio.mp3")
                if self.cover_path and os.path.exists(self.cover_path):
                    with Image.open(self.cover_path) as img:
                        img.save(os.path.join(temp_dir, "cover.webp"), format="WEBP")
                    zf.write(os.path.join(temp_dir, "cover.webp"), arcname="cover.webp")

            shutil.rmtree(temp_dir)
            self.progress_bar.set(1.0)
            self.update_status(f"✅ Success! Saved to {output_bfs}", "green")

        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", "red")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        finally:
            self.generate_btn.configure(state="normal", text="🚀 Generate Chart")

    def update_status(self, text, color):
        # Thread-safe UI update
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

if __name__ == "__main__":
    app = BFSApp()
    app.mainloop()

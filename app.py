import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
import json
import zipfile
import shutil
import random
import subprocess
import sys
import yt_dlp
import librosa
import numpy as np
from PIL import Image

# --- APP SETTINGS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

def sanitize_filename(name):
    clean = "".join(c for c in name if c not in r'\/:*?"<>|').strip()
    return clean if clean else "generated_chart"

def parse_osu_file(osu_path):
    bpm = 120.0
    hit_objects = []
    in_timing, in_objects = False, False
    with open(osu_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == "[TimingPoints]": in_timing, in_objects = True, False
            elif line == "[HitObjects]": in_timing, in_objects = False, True
            elif line.startswith("["): in_timing, in_objects = False, False
            if in_timing and line and not line.startswith("//"):
                parts = line.split(',')
                if len(parts) >= 2 and float(parts[0]) == 0.0:
                    ms_per_beat = float(parts[1])
                    if ms_per_beat > 0: bpm = 60000.0 / ms_per_beat
            if in_objects and line and not line.startswith("//"):
                parts = line.split(',')
                if len(parts) >= 3:
                    hit_objects.append({"x": int(parts[0]), "time_ms": int(parts[2])})
    return bpm, hit_objects

class BFSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Beat For Speed AI Chart Generator")
        self.geometry("750x700") # Made slightly taller for the checkbox
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self, text="🏍️ BFS AI Chart Generator", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(30, 10), padx=20)

        # YouTube URL Input
        self.url_label = ctk.CTkLabel(self, text="YouTube URL:", anchor="w")
        self.url_label.grid(row=1, column=0, pady=(10, 0), padx=40, sticky="w")
        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://www.youtube.com/watch?v=...", width=670)
        self.url_entry.grid(row=2, column=0, pady=10, padx=40)

        # Cover Image Input
        self.cover_label = ctk.CTkLabel(self, text="Cover Image (Optional):", anchor="w")
        self.cover_label.grid(row=3, column=0, pady=(10, 0), padx=40, sticky="w")
        self.cover_btn = ctk.CTkButton(self, text="Select Image", command=self.select_cover, width=150)
        self.cover_btn.grid(row=3, column=0, pady=10, padx=40, sticky="e")
        self.cover_path = ""

        # --- NEW: ENGINE SELECTION CHECKBOX ---
        self.use_heavy_ai_var = ctk.BooleanVar(value=False)
        self.heavy_ai_checkbox = ctk.CTkCheckBox(
            self,
            text="Use Heavy AI (Mapperatorinator) - Slow, High Quality (Requires GPU & Git)",
            variable=self.use_heavy_ai_var,
            hover_color="#333333"
        )
        self.heavy_ai_checkbox.grid(row=4, column=0, pady=10, padx=40, sticky="w")

        # Generate Button
        self.generate_btn = ctk.CTkButton(self, text="🚀 Generate Chart", command=self.start_generation, font=ctk.CTkFont(size=16, weight="bold"), height=50)
        self.generate_btn.grid(row=5, column=0, pady=30, padx=40)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=670)
        self.progress_bar.grid(row=6, column=0, pady=10, padx=40)
        self.progress_bar.set(0)

        # Status Log
        self.status_label = ctk.CTkLabel(self, text="Ready.", text_color="gray")
        self.status_label.grid(row=7, column=0, pady=(0, 30), padx=40)

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

        thread = threading.Thread(target=self.run_pipeline, args=(url,))
        thread.start()

    def run_pipeline(self, url):
        temp_dir = "temp_app_data"
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs("bfs", exist_ok=True)

        use_heavy = self.use_heavy_ai_var.get()

        try:
            # --- STEP 1: DOWNLOAD AUDIO ---
            self.update_status("1/5: Downloading audio from YouTube...", "#00d4ff")
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

            song_title = sanitize_filename(raw_title)
            audio_path = next((f for f in os.listdir(temp_dir) if f.endswith('.mp3')), None)
            if not audio_path: raise Exception("Audio download failed.")
            audio_path = os.path.join(temp_dir, audio_path)

            # --- STEP 2: GENERATE NOTES ---
            if use_heavy:
                self.update_status("2/5: Setting up Heavy AI (This may take a while)...", "#ffaa00")
                self.progress_bar.set(0.2)

                # 1. Clone if missing
                if not os.path.exists("Mapperatorinator"):
                    subprocess.run(["git", "clone", "https://github.com/OliBomby/Mapperatorinator.git"], check=True, capture_output=True)

                # 2. Run Inference
                self.update_status("2/5: Running Mapperatorinator AI...", "#ffaa00")
                cmd = [
                    sys.executable, "Mapperatorinator/inference.py",
                    f"audio_path={audio_path}",
                    f"output_path={temp_dir}",
                    "gamemode=3", "keycount=5", "difficulty=5"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"AI crashed. Check console. Error: {result.stderr[:100]}")

                osu_path = next((f for f in os.listdir(temp_dir) if f.endswith('.osu')), None)
                if not osu_path: raise Exception("AI didn't output an .osu file.")
                osu_path = os.path.join(temp_dir, osu_path)

                bpm, objects = parse_osu_file(osu_path)
                source_name = "Mapperatorinator"
            else:
                # LIGHTWEIGHT FALLBACK
                self.update_status("2/5: Analyzing audio (Fast/Lightweight Mode)...", "#00d4ff")
                self.progress_bar.set(0.3)
                y, sr = librosa.load(audio_path, sr=22050)
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                bpm = float(np.array(tempo).flatten()[0])
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
                onset_times = librosa.frames_to_time(onset_frames, sr=sr)
                onset_beats = (onset_times / 60.0) * bpm

                objects = []
                for beat in onset_beats:
                    humanized_beat = round(float(beat) + np.random.uniform(-0.02, 0.02), 4)
                    lane_index = random.randint(0, 4)
                    objects.append({"x": lane_index * 102.4, "time_ms": humanized_beat * (60.0 / bpm) * 1000})
                source_name = "Librosa Lightweight"

            # --- STEP 3: CONVERT TO BFS ---
            self.update_status("3/5: Adding smart obstacles & themes...", "#00d4ff")
            self.progress_bar.set(0.7)

            entities = [{"beat": 0.0, "key": 5, "datamodel": "custom_song_structure_gameplay/g00_s00_intro", "width": 0.25, "volume": 100}]

            for obj in objects:
                beat = (obj["time_ms"] / 1000.0) / (60.0 / bpm)
                lane_index = max(0, min(4, int(obj["x"] / 102.4)))
                entities.append({"beat": round(beat, 4), "key": 5 + lane_index, "datamodel": "custom_custom_spawn_cube/spawn_cube", "width": 0.25, "volume": 100})

            # Add 15 smart obstacles
            time_gaps = [objects[i]["time_ms"] - objects[i-1]["time_ms"] for i in range(1, len(objects))]
            avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 500
            intense = []
            for i, obj in enumerate(objects):
                if obj["time_ms"] > 5000 and i > 0:
                    current_gap = obj["time_ms"] - objects[i-1]["time_ms"]
                    if 0 < current_gap < (avg_gap * 0.7):
                        intense.append({"beat": (obj["time_ms"] / 1000.0) / (60.0 / bpm), "intensity": avg_gap / current_gap})

            intense.sort(key=lambda x: x["intensity"], reverse=True)
            for moment in intense[:15]:
                entities.append({"beat": round(moment["beat"], 4), "key": random.randint(5, 9), "datamodel": "custom_custom_spawn_cube/spawn_sting", "width": 0.25, "volume": 100})

            last_beat = (objects[-1]["time_ms"] / 1000.0) / (60.0 / bpm) if objects else 100
            entities.append({"beat": 0.0, "key": 1, "datamodel": "custom_themes/city_cold_night_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat * 0.25, 4), "key": 1, "datamodel": "custom_themes/city_blue_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat * 0.60, 4), "key": 1, "datamodel": "custom_themes/city_red_night_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat * 0.85, 4), "key": 1, "datamodel": "custom_themes/city_gold_theme", "width": 0.25, "volume": 100})
            entities.append({"beat": round(last_beat, 4), "key": 5, "datamodel": "custom_song_structure_gameplay/end", "width": 0.25, "volume": 100})
            entities.sort(key=lambda x: x["beat"])

            final_chart = {
                "musicData": {"filename": "", "bpm": round(bpm, 2), "runBeats": 0.0},
                "entities": entities,
                "editorMeta": {"axisMap": [1,0,0,0,0,0,0,0,0,0], "datamodelTypes": [], "songStructure": {"version": "v2", "mode": "gameplay_compact", "source": source_name}},
                "bfsMetadata": {
                    "songName": raw_title,
                    "artist": uploader,
                    "author": source_name,
                    "difficulty": "Medium",
                    "genre": "AI",
                    "description": f"Generated from {url}",
                    "coverFileName": "cover.webp"
                }
            }

            # --- STEP 4: PACKAGE ---
            self.update_status("4/5: Packaging .bfs file...", "#00d4ff")
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
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

if __name__ == "__main__":
    app = BFSApp()
    app.mainloop()

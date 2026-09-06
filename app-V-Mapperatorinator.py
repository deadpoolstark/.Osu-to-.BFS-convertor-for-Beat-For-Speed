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
import numpy as np
from PIL import Image

# --- APP SETTINGS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

def sanitize_filename(name):
    clean = "".join(c for c in name if c not in r'\/:*?"<>|').strip()
    return clean if clean else "generated_chart"

def parse_osu_file(osu_path):
    """Parses the AI-generated .osu file."""
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
        self.title("Beat For Speed AI Chart Generator (Mapperatorinator)")
        self.geometry("750x650")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.title_label = ctk.CTkLabel(self, text="🏍️ BFS AI Chart Generator", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(30, 10), padx=20)

        self.url_label = ctk.CTkLabel(self, text="YouTube URL:", anchor="w")
        self.url_label.grid(row=1, column=0, pady=(10, 0), padx=40, sticky="w")

        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://www.youtube.com/watch?v=...", width=670)
        self.url_entry.grid(row=2, column=0, pady=10, padx=40)

        self.cover_label = ctk.CTkLabel(self, text="Cover Image (Optional):", anchor="w")
        self.cover_label.grid(row=3, column=0, pady=(10, 0), padx=40, sticky="w")

        self.cover_btn = ctk.CTkButton(self, text="Select Image", command=self.select_cover, width=150)
        self.cover_btn.grid(row=3, column=0, pady=10, padx=40, sticky="e")
        self.cover_path = ""

        self.generate_btn = ctk.CTkButton(self, text=" Generate Chart", command=self.start_generation, font=ctk.CTkFont(size=16, weight="bold"), height=50)
        self.generate_btn.grid(row=4, column=0, pady=30, padx=40)

        self.progress_bar = ctk.CTkProgressBar(self, width=670)
        self.progress_bar.grid(row=5, column=0, pady=10, padx=40)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready. (First run will download the AI model)", text_color="gray")
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

        thread = threading.Thread(target=self.run_pipeline, args=(url,))
        thread.start()

    def run_pipeline(self, url):
        temp_dir = "temp_app_data"
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs("bfs", exist_ok=True)

        try:
            # --- STEP 0: ENSURE AI MODEL IS DOWNLOADED ---
            if not os.path.exists("Mapperatorinator"):
                self.update_status("0/5: Downloading Mapperatorinator AI Model (One-time setup)...", "#ffaa00")
                self.progress_bar.set(0.05)
                # Clone the repo
                subprocess.run(["git", "clone", "https://github.com/OliBomby/Mapperatorinator.git"], check=True)
                # Install its specific requirements
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "Mapperatorinator/requirements.txt"], check=True)

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

            # --- STEP 2: RUN THE HEAVY AI ---
            self.update_status("2/5: Running Mapperatorinator AI (This may take a few minutes)...", "#00d4ff")
            self.progress_bar.set(0.3)

            osu_output_path = os.path.join(temp_dir, "ai_map.osu")
            # Run the AI via command line
            cmd = [
                sys.executable, "Mapperatorinator/inference.py",
                f"audio_path={audio_path}",
                f"output_path={temp_dir}",
                "gamemode=3", "keycount=5", "difficulty=5"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("AI Error:", result.stderr)
                raise Exception("AI Generation failed. Check console for details.")

            osu_path = next((f for f in os.listdir(temp_dir) if f.endswith('.osu')), None)
            if not osu_path: raise Exception("AI didn't output an .osu file.")
            osu_path = os.path.join(temp_dir, osu_path)

            # --- STEP 3: PARSE & CONVERT TO BFS ---
            self.update_status("3/5: Parsing AI map & adding smart obstacles...", "#00d4ff")
            self.progress_bar.set(0.7)

            bpm, objects = parse_osu_file(osu_path)
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

            # Add Themes & End
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
                "editorMeta": {"axisMap": [1,0,0,0,0,0,0,0,0,0], "datamodelTypes": [], "songStructure": {"version": "v2", "mode": "gameplay_compact", "source": "Mapperatorinator_Local"}},
                "bfsMetadata": {
                    "songName": raw_title,
                    "artist": uploader,
                    "author": "Mapperatorinator AI",
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

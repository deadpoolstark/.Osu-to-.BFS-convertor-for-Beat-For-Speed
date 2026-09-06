import gradio as gr
import yt_dlp
import subprocess
import os
import json
import zipfile
import shutil
import random

# --- HELPER: Parse the generated .osu file ---
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

# --- MAIN PIPELINE ---
def generate_chart(youtube_url):
    temp_dir = "temp_process"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Download Audio
        gr.Info("Downloading audio from YouTube... (This may take 1-2 mins)")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{temp_dir}/audio.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        audio_path = next((f for f in os.listdir(temp_dir) if f.endswith('.mp3')), None)
        if not audio_path:
            return None, "Failed to download audio."
        audio_path = os.path.join(temp_dir, audio_path)

        # 2. Run Mapperatorinator AI
        gr.Info("Running AI to generate .osu map... (Please wait)")
        osu_output = os.path.join(temp_dir, "ai_map.osu")
        cmd = [
            "python", "Mapperatorinator/inference.py",
            f"audio_path={audio_path}",
            f"output_path={temp_dir}",
            "gamemode=3", "keycount=5", "difficulty=5"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        osu_path = next((f for f in os.listdir(temp_dir) if f.endswith('.osu')), None)
        if not osu_path:
            return None, "AI generation failed. Check console logs."
        osu_path = os.path.join(temp_dir, osu_path)

        # 3. Convert .osu to .bfs (Using our smart logic)
        gr.Info("Converting to Beat For Speed format with smart obstacles...")
        bpm, objects = parse_osu_file(osu_path)

        entities = [{"beat": 0.0, "key": 5, "datamodel": "custom_song_structure_gameplay/g00_s00_intro", "width": 0.25, "volume": 100}]

        for obj in objects:
            beat = (obj["time_ms"] / 1000.0) / (60.0 / bpm)
            lane_index = max(0, min(4, int(obj["x"] / 102.4)))
            entities.append({"beat": round(beat, 4), "key": 5 + lane_index, "datamodel": "custom_custom_spawn_cube/spawn_cube", "width": 0.25, "volume": 100})

        # Add max 15 smart obstacles
        time_gaps = [objects[i]["time_ms"] - objects[i-1]["time_ms"] for i in range(1, len(objects))]
        avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 500

        intense_moments = []
        for i, obj in enumerate(objects):
            if obj["time_ms"] > 5000 and i > 0:
                current_gap = obj["time_ms"] - objects[i-1]["time_ms"]
                if 0 < current_gap < (avg_gap * 0.7):
                    intense_moments.append({"beat": (obj["time_ms"] / 1000.0) / (60.0 / bpm), "intensity": avg_gap / current_gap})

        intense_moments.sort(key=lambda x: x["intensity"], reverse=True)
        for moment in intense_moments[:15]:
            entities.append({"beat": round(moment["beat"], 4), "key": random.randint(5, 9), "datamodel": "custom_custom_spawn_cube/spawn_sting", "width": 0.25, "volume": 100})

        # Add Themes & End
        last_beat = (objects[-1]["time_ms"] / 1000.0) / (60.0 / bpm) if objects else 100
        entities.append({"beat": 0.0, "key": 1, "datamodel": "custom_themes/city_cold_night_theme", "width": 0.25, "volume": 100})
        entities.append({"beat": round(last_beat, 4), "key": 5, "datamodel": "custom_song_structure_gameplay/end", "width": 0.25, "volume": 100})
        entities.sort(key=lambda x: x["beat"])

        final_chart = {
            "musicData": {"filename": "", "bpm": round(bpm, 2), "runBeats": 0.0},
            "entities": entities,
            "editorMeta": {"axisMap": [1,0,0,0,0,0,0,0,0,0], "datamodelTypes": [], "songStructure": {"version": "v2", "mode": "gameplay_compact", "source": "YT_AI_Pipeline"}},
            "bfsMetadata": {"songName": "YT AI Gen", "artist": "Unknown", "author": "Auto", "difficulty": "Medium", "genre": "AI", "description": f"Generated from {youtube_url}", "coverFileName": "cover.webp"}
        }

        # 4. Package and Return
        output_bfs = os.path.join(temp_dir, "final_chart.bfs")
        with zipfile.ZipFile(output_bfs, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("chart.json", json.dumps(final_chart, indent=2))
            zf.write(audio_path, arcname="audio.mp3")
            # Create a dummy cover if you don't have one
            with open("dummy_cover.webp", "wb") as f: pass # Placeholder
            if os.path.exists("dummy_cover.webp"):
                zf.write("dummy_cover.webp", arcname="cover.webp")

        # Cleanup
        shutil.rmtree(temp_dir)
        gr.Info("✅ Success! Downloading your .bfs file.")
        return output_bfs, "Chart generated successfully!"

    except Exception as e:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return None, f"Error: {str(e)}"

# --- GRADIO UI ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as demo:
    gr.Markdown("# 🏍️ YouTube to Beat For Speed AI Converter")
    gr.Markdown("Paste a YouTube link. The server will download the audio, run the Mapperatorinator AI, add 15 smart obstacles, and give you a ready-to-play `.bfs` file.")

    with gr.Row():
        with gr.Column():
            yt_input = gr.Textbox(label="YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
            submit_btn = gr.Button("🚀 Generate Chart", variant="primary")
        with gr.Column():
            status_output = gr.Textbox(label="Status", interactive=False)
            file_output = gr.File(label="Download .bfs Chart")

    submit_btn.click(
        fn=generate_chart,
        inputs=[yt_input],
        outputs=[file_output, status_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

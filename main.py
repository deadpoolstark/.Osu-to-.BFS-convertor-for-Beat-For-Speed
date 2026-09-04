from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import json, zipfile, io, random, os, tempfile

app = FastAPI()

# --- YOUR EXACT PARSING LOGIC ---
def parse_osu_file(osu_content: str):
    bpm = 120.0
    hit_objects = []
    in_timing, in_objects = False, False
    
    for line in osu_content.splitlines():
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

# --- THE WEB ENDPOINT ---
@app.post("/convert")
async def convert_to_bfs(
    osu_file: UploadFile = File(...), 
    audio_file: UploadFile = File(...), 
    image_file: UploadFile = File(...)
):
    try:
        # 1. Read the uploaded files
        osu_content = (await osu_file.read()).decode('utf-8')
        audio_content = await audio_file.read()
        image_content = await image_file.read()
        
        # 2. Run your conversion logic
        bpm, objects = parse_osu_file(osu_content)
        
        time_gaps = [objects[i]["time_ms"] - objects[i-1]["time_ms"] for i in range(1, len(objects))]
        avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 500
        
        entities = [{"beat": 0.0, "key": 5, "datamodel": "custom_song_structure_gameplay/g00_s00_intro", "width": 0.25, "volume": 100}]
        
        for obj in objects:
            beat = (obj["time_ms"] / 1000.0) / (60.0 / bpm)
            lane_index = max(0, min(4, int(obj["x"] / 102.4)))
            entities.append({"beat": round(beat, 4), "key": 5 + lane_index, "datamodel": "custom_custom_spawn_cube/spawn_cube", "width": 0.25, "volume": 100})

        # Add max 15 obstacles
        intense_moments = []
        for i, obj in enumerate(objects):
            if obj["time_ms"] > 5000 and i > 0:
                current_gap = obj["time_ms"] - objects[i-1]["time_ms"]
                if 0 < current_gap < (avg_gap * 0.7):
                    intense_moments.append({"beat": (obj["time_ms"] / 1000.0) / (60.0 / bpm), "intensity": avg_gap / current_gap})
        
        intense_moments.sort(key=lambda x: x["intensity"], reverse=True)
        for moment in intense_moments[:15]:
            entities.append({"beat": round(moment["beat"], 4), "key": random.randint(5, 9), "datamodel": "custom_custom_spawn_cube/spawn_sting", "width": 0.25, "volume": 100})

        # Add Themes & End Marker
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
            "editorMeta": {"axisMap": [1,0,0,0,0,0,0,0,0,0], "datamodelTypes": [], "songStructure": {"version": "v2", "mode": "gameplay_compact", "source": "Web_Converter"}},
            "bfsMetadata": {"songName": "Web Generated", "artist": "AI", "author": "Web", "difficulty": "Medium", "genre": "AI", "description": "Generated via Web", "coverFileName": "cover.webp"}
        }

        # 3. Create the .bfs ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("chart.json", json.dumps(final_chart, indent=2))
            zf.writestr("audio.mp3", audio_content)
            zf.writestr("cover.webp", image_content)
        
        zip_buffer.seek(0)
        
        # 4. Send the file back to the user
        return FileResponse(
            zip_buffer.getvalue(), 
            media_type="application/zip", 
            headers={"Content-Disposition": "attachment; filename=chart.bfs"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
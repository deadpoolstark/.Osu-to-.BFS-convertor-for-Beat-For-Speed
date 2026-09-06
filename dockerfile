FROM python:3.10-slim

# Install system dependencies (ffmpeg is REQUIRED for yt-dlp to convert audio)
RUN apt-get update && apt-get install -y ffmpeg git

WORKDIR /app

# Clone the AI generator directly into the container
RUN git clone https://github.com/OliBomby/Mapperatorinator.git

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r Mapperatorinator/requirements.txt

COPY . .

# Expose the port Hugging Face expects
EXPOSE 7860

# Run the Gradio app
CMD ["python", "app.py"]

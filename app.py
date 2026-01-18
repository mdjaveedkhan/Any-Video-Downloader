from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import shutil

app = Flask(__name__)

# Temporary folder to hold files before they are sent to the user
DOWNLOAD_FOLDER = "temp_downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    format_type = request.form.get("format")
    quality = request.form.get("quality")

    if not url:
        return "URL is required", 400
    # Options for yt-dlp
    ydl_opts = {
        # Using a template that ensures we know where the file goes
        # "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        # "restrictfilenames": True,
        # "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title).50s.%(ext)s",
        "noplaylist": True,
        "quiet": False,  # Turn on logs to see what's happening
        "restrictfilenames": True,
        "source_address": "0.0.0.0"
         # Bypass settings
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    COOKIES_PATH = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    # Add cookies if the file exists
    if os.path.exists(COOKIES_PATH):
        ydl_opts["cookiefile"] = COOKIES_PATH
        print("✅ Cookie file detected and loaded.")
    else:
        print("❌ cookies.txt NOT FOUND! YouTube will likely block this request.")    
if format_type == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        if quality == "best":
            ydl_opts["format"] = "bestvideo+bestaudio/best"
        else:
            ydl_opts["format"] = f"bestvideo[height<={quality}]+bestaudio/best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get the final filename
            info = ydl.extract_info(url, download=True)
            # Get the path of the downloaded file
            file_path = ydl.prepare_filename(info)
            
            # If it was an MP3, the extension changed from the original
            if format_type == "mp3":
                file_path = os.path.splitext(file_path)[0] + ".mp3"

        # This helper function deletes the file after the user downloads it
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up: {e}")
            return response

        # send_file triggers the browser's "Save As" dialog
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return str(e), 500

if __name__ == "__main__":

    app.run(debug=True)




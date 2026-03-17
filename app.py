import subprocess
import threading
import os
from flask import Flask, Response, send_from_directory

app = Flask(__name__)

ZEE_URL = "https://z5ak-cmaflive.zee5.com/cmaf/live/2105545/ZeeTeluguHDELE/index.m3u8?hdnea=st=1773769836~exp=1773770136~acl=*~id=78c2f46e-03f9-456c-8e2a-7b2460936af0~hmac=f100bfa16fe52b69fef7ac0224013ea909094ab92de2f6bb6db7d5182faffcaa&originpath=/linear/hls/pb/event/c5sgyUOqSDSDUzovvmBwAA/stream/a9e2d310-f2fa-49f2-9512-7585dc51c9eb:SIN2/master.m3u8"

HEADERS = 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36\r\nReferer: https://www.zee5.com/\r\nOrigin: https://www.zee5.com\r\n'

HLS_DIR = "/tmp/zee-hls"
os.makedirs(HLS_DIR, exist_ok=True)

def run_ffmpeg():
    while True:
        process = subprocess.Popen([
            'ffmpeg', '-y',
            '-headers', HEADERS,
            '-i', ZEE_URL,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '10',
            '-hls_list_size', '6',
            '-hls_flags', 'delete_segments',
            os.path.join(HLS_DIR, 'index.m3u8')
        ], stderr=subprocess.DEVNULL)
        process.wait()

threading.Thread(target=run_ffmpeg, daemon=True).start()

@app.route('/zee/index.m3u8')
def serve_playlist():
    filepath = os.path.join(HLS_DIR, 'index.m3u8')
    if os.path.exists(filepath):
        return send_from_directory(HLS_DIR, 'index.m3u8', mimetype='application/vnd.apple.mpegurl')
    return "Stream starting, try again in 15 seconds...", 503

@app.route('/zee/<filename>')
def serve_segment(filename):
    return send_from_directory(HLS_DIR, filename, mimetype='video/mp2t')

@app.route('/')
def index():
    return '''
    <html><head>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    </head><body>
    <h2>Zee Telugu Video Relay</h2>
    <video id="video" controls width="640" height="360"></video>
    <br><br>
    <b>ACRCloud URL:</b> <code>/zee/index.m3u8</code>
    <script>
    var video = document.getElementById('video');
    if (Hls.isSupported()) {
        var hls = new Hls();
        hls.loadSource('/zee/index.m3u8');
        hls.attachMedia(video);
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = '/zee/index.m3u8';
    }
    </script>
    </body></html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

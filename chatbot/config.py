import os 

#Bot token 
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

#Authorized users
CHAT_IDS = [
    1969139002,
    1430460059,
    52338470,
    987449095,
    471938014,
]

# Klipper base URL
KLIPPER_BASE_URL = "http://192.168.31.100:7125"

# GStreamer pipeline
GST_PIPELINE = [
    'gst-launch-1.0',
    '-v',
    'v4l2src',
    'device=/dev/video0',
    '!', 'image/jpeg,width=1920,height=1080,framerate=30/1',
    '!', 'jpegdec',
    '!', 'videoconvert',
    '!', 'x264enc',
    'tune=zerolatency',
    'bitrate=2000',
    'speed-preset=superfast',
    '!', 'flvmux',
    'streamable=true',
    '!', 'rtmpsink',
    'location=rtmp://localhost/live/stream',
]

STREAM_URL = "http://192.168.31.109:8080/"


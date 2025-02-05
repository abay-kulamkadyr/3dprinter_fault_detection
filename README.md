# 3D Printer Camera Capture and Chatbot Control System

The **3D Printer Camera Capture and Chatbot Control System** is a solution that lets you monitor and control your 3D printer remotely using Telegram and a live camera stream. The system integrates printer control via the Klipper API, a fault detection system using Detectron2 for object detection, and live video streaming via Nginx with the RTMP module.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation Instructions](#installation-instructions)
  - [1. System Packages and Nginx with RTMP Module](#1-system-packages-and-nginx-with-rtmp-module)
  - [2. Python Environment and .env Setup](#2-python-environment-and-env-setup)
  - [3. OpenCV-Python with GStreamer Support](#3-opencv-python-with-gstreamer-support)
  - [4. Detectron2 Installation](#4-detectron2-installation)
- [Usage](#usage)
  - [Chatbot & Flask Server](#chatbot--flask-server)
  - [Fault Detection System](#fault-detection-system)
  - [Live Video Streaming](#live-video-streaming)
- [Additional Information](#additional-information)
- [License](#license)

---

## Overview

This project has two main components:

1. **Chatbot Component**:  
   A Telegram bot that interacts with users to provide printer status, printer control commands (e.g., pause, resume, emergency stop), and a live stream of your printer. It communicates with the Klipper API and uses a Flask server to receive detection alerts.

2. **Fault Detection Component**:  
   A system that uses a camera and object detection (via Detectron2) to monitor your 3D print. When a fault is detected, the system saves an image, sends a notification to the Flask endpoint, and the chatbot then alerts authorized users.

---

## Features

- **Remote Printer Control**:  
  Check printer status, monitor temperatures, pause/resume prints, and execute emergency actions.

- **Live Video Streaming**:  
  View a live video feed of your printer using a browser-friendly HLS stream delivered by Nginx with the RTMP module.

- **Fault Detection**:  
  Automatically detect print failures using Detectron2 and notify you with an image snapshot.

- **Interactive Boundary Selection**:  
  Define a region of interest (ROI) within the camera frame to focus detection on the critical area.

---

## Prerequisites

- **Operating System**: Raspberry Pi OS or another Debian-based distribution  
- **Hardware**: Raspberry Pi (e.g., Raspberry Pi 5 Model B Rev 1.0) with a camera device  
- **Python**: Version 3.7 or later  
- **System Tools**: `git`, `pip`, `virtualenv`

---

## Installation Instructions

### 1. System Packages and Nginx with RTMP Module

Install **Nginx** and the RTMP module (for live streaming):

```bash
sudo apt update
sudo apt install nginx
sudo apt install libnginx-mod-rtmp

Then, configure Nginx by editing /etc/nginx/nginx.conf to include the RTMP settings. For example:

include /etc/nginx/modules-enabled/*.conf;

worker_processes  auto;
events {
    worker_connections  1024;
}

http {
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout  65;
    types_hash_max_size 2048;

    include         mime.types;
    default_type    application/octet-stream;

    server {
        listen 8080;
        server_name localhost;

        location / {
            root   html;
            index  index.html index.htm;
        }

        # HLS streaming
        location /hls {
            types {
                application/vnd.apple.mpegurl m3u8;
                video/mp2t ts;
            }
            root /tmp;
            add_header Cache-Control no-cache;
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length, Content-Range' always;

            # Enable CORS for OPTIONS requests
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }
        }
    }
}

rtmp {
    server {
        listen 1935;  # RTMP listen port
        chunk_size 4096;

        application live {
            live on;
            record off;

            # HLS settings
            hls on;
            hls_path /tmp/hls;
            hls_fragment 2;
            hls_playlist_length 15;
        }
    }
}
```
The default public web location is /usr/share/nginx/html with an index.html file that can display your live stream.

Example index.html:
```bash
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Live 3D Printer Stream</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f0f0f0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    video {
      border: 2px solid #333;
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <h1>Live 3D Printer Camera Stream</h1>
  <video id="video" controls autoplay width="1280" height="720"></video>

  <script>
    document.addEventListener("DOMContentLoaded", function () {
      var video = document.getElementById('video');
      var videoSrc = 'http://192.168.31.109:8080/hls/stream.m3u8';

      if (Hls.isSupported()) {
        var hls = new Hls();
        hls.loadSource(videoSrc);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function () {
          video.play();
        });
      }
      else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', function () {
          video.play();
        });
      }
      else {
        console.error("This browser does not support HLS.");
      }
    });
  </script>
</body>
</html>
```
Restart Nginx after making changes:
```bash
sudo systemctl restart nginx
```
2. Python Environment and .env Setup

Create a Python virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create a .env file (or export in your shell) with your Telegram bot token:
```bash
export BOT_TOKEN=YOUR_TOKEN
```

3. OpenCV-Python with GStreamer Support

The project includes a guide to build OpenCV with GStreamer support. Follow follow instructions in the README.md of the `scripts` directory


4. Detectron2 Installation

Install Detectron2 with the following command:

```bash
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
```

## Usage
### Chatbot & Flask Server

    Start the Bot and Flask Server:
    From the chatbot/ directory, run:

```bash
    python main.py
```
    The Telegram bot will start polling and the Flask server will run on port 5000 to accept detection alerts.

    Interact via Telegram:
    Use commands (e.g., /start, /info, /pause, etc.) to control and monitor your printer.

### Fault Detection System

    Start the Detection System:
    From the src/ directory, run:

```bash
    python main.py

```
    The system will capture camera frames, perform object detection, save images upon fault detection, and notify the Flask server.

### Live Video Streaming

    Stream Setup:
    The RTMP application defined in your Nginx configuration listens on port 1935. Your camera streaming software should push the stream to the live application.
    Viewing the Stream:
    Open your browser and go to:

    http://<your_pi_ip>:8080

    You should see the index page with a live HLS stream.

## Additional Information

    Environment Variables:
    Ensure that your environment variable BOT_TOKEN is set correctly. You can place it in a .env file or export it in your shell.

    Scripts Directory:
    The scripts directory contains helper shell scripts to install GStreamer dependencies, OpenCV dependencies, and Detectron2. Refer to scripts/README.md for more details.

    Logs and Debugging:
    Check the logs output by the Python scripts for any errors during runtime. The chatbot and detection system log messages using Python’s logging module.

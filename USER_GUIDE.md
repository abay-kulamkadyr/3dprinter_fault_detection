# 3D Printer Chatbot & Live Stream User Guide

Welcome to your 3D Printer Chatbot and Live Stream System! This guide will help you understand what the system does and how to use it—all without needing any technical expertise.

---

## What Does This System Do?

- **Remote Printer Control:**  
  You can check your printer’s status, pause/resume a print, or even stop the printer immediately in an emergency—all from your Telegram app.

- **Live Camera Stream:**  
  Watch your printer in real time via a live video feed in your web browser.

- **Fault Detection Alerts:**  
  If the system detects a problem with your print, it automatically sends you a picture of the issue so you can take action quickly.

---

## How Do I Get Started?

### 1. Chatbot on Telegram

- **Start the Chat:**  
  Open Telegram and find the chatbot (your administrator will share its name or link). When you start chatting, you’ll see a friendly welcome message with several buttons.

- **Using the Buttons:**  
  Tap the buttons to do things like:
  - **View Printer Status:** See an instant snapshot of your printer and get updates about what’s happening.
  - **Monitor Temperatures:** Check the current and target temperatures of your printer’s bed and extruder.
  - **Control the Print:** Pause, resume, or send emergency commands (you’ll be asked to confirm these commands to prevent mistakes).
  - **Live Stream:** Start or stop the live video feed of your printer.

### 2. Viewing the Live Video Stream

- **Setup:**  
  The system uses a web server (Nginx) that has been set up to handle live video. This part of the system streams your camera’s view of the printer.

- **How to Watch:**  
  Open your web browser and visit the URL provided by your administrator (for example, `http://<your_pi_ip>:8080`). You’ll see a simple webpage with a video player that automatically starts the live stream.

### 3. Fault Detection Alerts

- **Automatic Alerts:**  
  The system continuously watches your printer using its camera. If it detects a problem (like a print failure), it takes a snapshot and sends you a notification via Telegram.
  
- **What You Receive:**  
  The alert message will include a picture of the problem and a short description, so you know exactly what happened.

---

## What’s Involved in the Setup? (For Your Administrator)

*This section is just an overview; you don't need to worry about these details if you're just using the system.*

- **Nginx with RTMP Module:**  
  The system uses Nginx (a web server) along with an RTMP module for live streaming. Your administrator has installed Nginx and added special settings so that your camera feed is converted into a web-friendly stream.

- **Python & Environment:**  
  The software runs in a Python virtual environment. Your administrator sets an environment variable with the bot’s token so that only authorized users can control and monitor the printer.

- **OpenCV with GStreamer Support:**  
  OpenCV (a tool for handling images and video) is built with GStreamer support so that it works smoothly with your camera hardware.

- **Detectron2 for Fault Detection:**  
  Detectron2, an advanced image recognition tool, watches for any print issues and triggers alerts when something isn’t right.

For detailed technical setup, your administrator can refer to the README files and scripts provided in the project.

---

## Quick Tips for a Great Experience

- **Keep the Chat Open:**  
  To receive real-time updates, keep your Telegram chat with the bot open.

- **Follow On-Screen Instructions:**  
  When you tap a button, the bot will guide you through any confirmations needed—this helps prevent accidental actions.

- **Check the Live Stream:**  
  Open your web browser on any device connected to your network and visit the provided URL to see your printer live.

- **Respond to Alerts:**  
  When you receive an alert, check the image and use the bot’s commands to take the appropriate action.

---

## Need Help?

If you have any questions or run into any issues, please contact your support team. Enjoy the convenience of controlling and monitoring your 3D printer from anywhere!

---

*Happy Printing!*

# OpenCV-Python Installation with GStreamer Support

This guide provides instructions to install OpenCV-Python with GStreamer support on **Raspberry Pi 5 Model B Rev 1.0**. Follow the steps below to set up the environment.

---



---

## System Compatibility

This installation process is tailored for the following hardware:

**Model**: Raspberry Pi 5 Model B Rev 1.0
**Operating System**: Raspberry Pi OS (or other compatible Debian-based distributions)

---

## Prerequisites

Ensure the following are installed on your system before proceeding:
- Python 3.x
- `pip` and `virtualenv`
- `git`

---

## Installation Steps

### Step 1: Install GStreamer Dependencies

Navigate to the `scripts` directory and run the script:
```bash
sudo chmod +x gstreamer_install.sh
./gstreamer_install.sh
```

This script installs the necessary GStreamer libraries and plugins.

---

### Step 2: Install OpenCV Dependencies

Navigate to the `scripts` directory and run:
```bash
sudo chmod +x install_opencv_dependencies.sh
./install_opencv_dependencies.sh
```

This script installs dependencies required to build OpenCV.

---

### Step 3: Build and Install OpenCV with GStreamer Support

Follow these steps to clone, modify, build, and install OpenCV-Python with GStreamer support:

1. Create a temporary directory for the build process:
   ```bash
   TMPDIR=$(mktemp -d)
   cd "${TMPDIR}"
   ```

2. Clone the OpenCV-Python repository:
   ```bash
   OPENCV_VER="master"
   git clone --branch ${OPENCV_VER} --depth 1 --recurse-submodules --shallow-submodules https://github.com/opencv/opencv-python.git opencv-python-${OPENCV_VER}
   ```

3. Modify the `ffmpeg_codecs.hpp` file to ensure compatibility with FFmpeg:
   ```bash
   cd opencv-python-${OPENCV_VER}
   sed -i '62a #include <libavcodec/version.h>' path/to/ffmpeg_codecs.hpp
   ```

4. Set up build configurations:
   ```bash
   export ENABLE_CONTRIB=0
   export CMAKE_ARGS="-DWITH_GSTREAMER=ON -DWITH_GTK=ON"
   ```

5. Build the OpenCV wheel:
   ```bash
   python3 -m pip wheel . --verbose --no-build-isolation
   ```

6. Install the OpenCV wheel:
   ```bash
   python3 -m pip install opencv_python*.whl
   ```

---

## Verification

To verify the installation:
1. Open a Python shell.
2. Run the following code:
```python
import cv2
print(cv2.getBuildInformation())
```
3. Ensure GStreamer support is enabled in the output.

---

## Troubleshooting

- Ensure all prerequisites are installed.
- Clean the build directory if re-installing:
  ```bash
  rm -rf /tmp/opencv_build
  ```

---

## Notes

This process has been tested specifically on the **Raspberry Pi 5 Model B Rev 1.0**. Compatibility with other hardware or operating systems may require adjustments.

---

## License

This project is distributed under the MIT License.


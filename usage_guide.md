# Usage Guide

Complete step-by-step instructions for running the system.

---

## 🚀 Quick Start (5 Minutes)

### Option 1: Use Sample Video

```bash
# 1. Download project
git clone https://github.com/yourusername/2wheeler-blind-spot-adas.git
cd 2wheeler-blind-spot-adas

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download YOLO model
python download_models.py

# 4. Generate warning sound
python sound_generator.py

# 5. Download sample video
# (Use any dashcam video from YouTube/Pexels)

# 6. Split video
python video_simulator.py
# Enter: your_video.mp4

# 7. Run detection
python main.py
# Choose: 1 (left side)
# Enter: videos/your_video_left.mp4
```

### Option 2: Use Webcam

```bash
# Steps 1-4 same as above

# 5. Run with webcam
python main.py
# Choose: 1
# Enter: 0  (webcam index)
```

---

## 📖 Detailed Instructions

### Step 1: Environment Setup

**Check Python version:**
```bash
python --version
# Should be 3.7 or higher
```

**Create virtual environment (recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install opencv-python numpy pygame
```

### Step 2: Download YOLO Model

**Automatic (recommended):**
```bash
python download_models.py
```

**Manual:**
1. Go to https://pjreddie.com/media/files/yolov3.weights
2. Download `yolov3.weights` (237 MB)
3. Place in project root

Download config files:
```bash
# yolov3.cfg
wget https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg

# coco.names
wget https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names
```

**Verify files:**
```bash
ls -lh yolov3.weights yolov3.cfg coco.names
```

Should see:
```
-rw-r--r-- 1 user user 237M yolov3.weights
-rw-r--r-- 1 user user  8.3K yolov3.cfg
-rw-r--r-- 1 user user   625 coco.names
```

### Step 3: Generate Audio

```bash
python sound_generator.py
```

Output:
```
✓ Warning sound generated: sounds/warning_beep.wav
```

### Step 4: Prepare Test Videos

#### Method A: Use Existing Dashcam Video

1. **Place video in `videos/` folder:**
   ```bash
   cp ~/Downloads/dashcam.mp4 videos/
   ```

2. **Split into left/right views:**
   ```bash
   python video_simulator.py
   ```
   
   When prompted:
   ```
   Video filename (e.g., dashcam.mp4): dashcam.mp4
   ```

3. **Output files created:**
   ```
   videos/dashcam_left.mp4
   videos/dashcam_right.mp4
   ```

#### Method B: Record from Webcam

```python
# record_test.py
import cv2

cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('videos/test.mp4', fourcc, 20.0, (640, 480))

print("Recording 30 seconds... Move objects around!")
for i in range(600):  # 30 seconds @ 20fps
    ret, frame = cap.read()
    if ret:
        out.write(frame)
        cv2.imshow('Recording', frame)
        cv2.waitKey(50)

cap.release()
out.release()
cv2.destroyAllWindows()
print("Saved to videos/test.mp4")
```

Run:
```bash
python record_test.py
python video_simulator.py  # Enter: test.mp4
```

### Step 5: Run Detection

```bash
python main.py
```

**Menu:**
```
============================================================
  🏍️ ADVANCED BLIND SPOT DETECTION v2.0
  Features: Motion Tracking | Trajectory Prediction
============================================================

Select Mode:
1. Single Camera (Left side)
2. Single Camera (Right side)
3. Exit

Enter choice (1-3): 
```

**Choose option 1 (left side):**
```
Enter left video path: videos/dashcam_left.mp4
```

**Output:**
```
Loading AI model...
✓ Advanced detection system initialized
Processing left side: 640x360 @ 30 FPS

🏍️ Processing Blind Spot Detection...
Press 'q' to quit
```

### Step 6: Interpret Output

**Window displays:**
- **Zones**: Colored overlays (red=critical, orange=warning, blue=self)
- **Detections**: Bounding boxes around vehicles
- **Motion vectors**: Arrows showing direction/speed
- **Status**: Bottom text shows threat level

**Console output:**
```
✓ Processed 1563 frames
```

**Saved file:**
```
output/left_advanced.mp4
```

---

## 🎛️ Configuration

### Adjust Detection Sensitivity

Edit `main.py` line 452:
```python
# More sensitive (more detections, more false positives)
if confidence > 0.3 and class_id in self.vehicle_classes:

# Less sensitive (fewer detections, might miss vehicles)
if confidence > 0.7 and class_id in self.vehicle_classes:
```

### Adjust Zone Boundaries

Edit `main.py` line 174-175:
```python
# Wider critical zone (more warnings)
self.base_critical = (0, int(0.45 * frame_width))

# Narrower critical zone (fewer warnings)
self.base_critical = (0, int(0.25 * frame_width))
```

### Adjust Self-Zone

Edit `main.py` line 180-185:
```python
self.self_zone = (
    int(0.7 * frame_width),   # Adjust if still detecting own bike
    int(0.6 * frame_height),  # Raise if mirror is higher in frame
    frame_width,
    frame_height
)
```

### Adjust Warning Cooldown

Edit `main.py` line 443:
```python
# More frequent warnings
self.warning_cooldown = 0.5  # seconds

# Less frequent warnings
self.warning_cooldown = 3.0  # seconds
```

---

## 🐛 Troubleshooting

### Error: "yolov3.weights not found"

**Solution:**
```bash
python download_models.py
# Or download manually from pjreddie.com
```

### Error: "No module named 'cv2'"

**Solution:**
```bash
pip install opencv-python
```

### Error: "No module named 'pygame'"

**Solution:**
```bash
pip install pygame
```

### Video not opening

**Check file path:**
```python
import os
print(os.path.exists("videos/dashcam_left.mp4"))
# Should print: True
```

**Check video codec:**
```bash
# Install ffmpeg if needed
# Then convert video:
ffmpeg -i input.mp4 -c:v libx264 output.mp4
```

### Slow processing (< 5 FPS)

**Solutions:**
1. Reduce video resolution:
   ```bash
   ffmpeg -i input.mp4 -vf scale=640:360 output.mp4
   ```

2. Use GPU acceleration (if NVIDIA GPU available):
   ```bash
   pip install opencv-contrib-python
   ```
   
   Edit `main.py` line 429:
   ```python
   self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
   self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
   ```

3. Skip frames:
   ```python
   # Process every 2nd frame
   if frame_count % 2 == 0:
       process_frame()
   ```

### False positives (detecting own vehicle)

**Solution:** Adjust self-zone boundaries

1. Run system and note where false detections occur
2. Edit `main.py` line 180-185
3. Expand self-zone to cover false positive area

### Not detecting vehicles

**Causes:**
- Video too dark → Try CLAHE enhancement
- Vehicles too small → Lower confidence threshold
- Unusual angle → System trained on road-level views

**Solutions:**
1. Lower confidence:
   ```python
   if confidence > 0.3:  # Instead of 0.5
   ```

2. Check vehicle classes:
   ```python
   print(self.classes[class_id])  # See what's being detected
   ```

---

## 📊 Performance Optimization

### For Raspberry Pi

```python
# main.py line 447
# Reduce resolution
blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), ...)

# Process every Nth frame
if frame_count % 3 == 0:
    detections = self.detect_vehicles(frame)
```

### For High-Resolution Video

```python
# Resize before processing
frame = cv2.resize(frame, (640, 360))
```

### For Real-Time (Webcam)

```python
# Skip older frames
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```

---

## 💾 Saving Output

### Save processed video

Already done automatically! Check `output/` folder.

### Save detection log

Add to `main.py`:
```python
# In process_side_view(), after threat classification:
with open('detection_log.txt', 'a') as f:
    f.write(f"{frame_count},{threat_level},{reason}\n")
```

### Export statistics

```python
# After processing completes:
import json
stats = {
    'total_frames': frame_count,
    'critical_events': critical_count,
    'warning_events': warning_count,
    'avg_fps': avg_fps
}
with open('stats.json', 'w') as f:
    json.dump(stats, f, indent=2)
```

---

## 🎓 Learning Exercises

### Beginner: Modify Thresholds
1. Change confidence from 0.5 to 0.3
2. Run on same video
3. Compare number of detections

### Intermediate: Add FPS Counter
```python
# Add to draw loop:
start = time.time()
# ... processing ...
fps = 1 / (time.time() - start)
cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), ...)
```

### Advanced: Implement Lane Detection
```python
def detect_lanes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50)
    return lines
```

---

## 📧 Support

If you encounter issues:
1. Check [Troubleshooting](#-troubleshooting) section
2. Search [GitHub Issues](https://github.com/yourusername/repo/issues)
3. Create new issue with:
   - Error message
   - System info (OS, Python version)
   - Steps to reproduce

Happy coding! 🚀

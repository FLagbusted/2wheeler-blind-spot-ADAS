# Known Issues & Limitations

This document lists known issues, their causes, and workarounds.

---

## 🔴 **Critical Issues**

### Issue #1: Camera Shake Causes False Detections

**Symptom:**
- Own vehicle (handlebar, mirror) gets detected as threat
- Random critical warnings when riding on bumpy roads
- Self-zone filter fails during heavy vibration

**Root Cause:**
The self-zone is defined by fixed pixel coordinates:
```python
self.self_zone = (
    int(0.7 * frame_width),   # Bottom-right corner
    int(0.6 * frame_height),
    frame_width,
    frame_height
)
```

When camera shakes, vehicle parts move **outside** the blue self-zone box, so the system thinks they're external vehicles.

**Visual Example:**

**Normal (No Shake):**
```
┌─────────────────────────────┐
│                             │
│         [Road]              │
│                             │
│                 ┌───────────┤
│                 │ 🔵 SELF   │ ← Mirror stays inside
└─────────────────┴───────────┘
```

**During Shake:**
```
┌─────────────────────────────┐
│                             │
│         [Road]              │
│              ┌──────────────┤
│         🪞   │ 🔵 SELF      │ ← Mirror moved outside!
└──────────────┴──────────────┘
          ↑ Gets detected as vehicle
```

**Evidence from Screenshots:**
- Image 2 (Left side): Shows self-zone at bottom, but parts still leak out
- Image 4: Heavy motion blur indicates camera shake

**Impact:**
- High false positive rate on rough roads
- Annoying audio spam
- User loses trust in system

**Current Workarounds:**

1. **Expand Self-Zone** (Temporary fix)
   ```python
   # main.py line 180
   self.self_zone = (
       int(0.6 * frame_width),   # Wider (was 0.7)
       int(0.5 * frame_height),  # Higher (was 0.6)
       frame_width,
       frame_height
   )
   ```
   **Trade-off:** Might ignore actual vehicles that enter from bottom

2. **Add Motion Blur Detection**
   ```python
   def is_frame_shaking(frame, prev_frame):
       # Calculate frame difference
       diff = cv2.absdiff(frame, prev_frame)
       blur_score = cv2.Laplacian(diff, cv2.CV_64F).var()
       
       if blur_score > SHAKE_THRESHOLD:
           return True  # Skip this frame
       return False
   ```

3. **Use Temporal Consistency**
   ```python
   # Only trust detections that persist for 3+ frames
   if detection_appears_in_last_n_frames(vehicle_id, n=3):
       classify_threat()
   else:
       ignore_detection()
   ```

**Proper Solution (Future Work):**

**Option A: Stabilize Camera Feed**
```python
# Using optical flow
prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Find transformation matrix
transform = cv2.estimateRigidTransform(prev_gray, curr_gray, False)

# Stabilize current frame
stabilized = cv2.warpAffine(frame, transform, (width, height))
```

**Option B: Dynamic Self-Zone with IMU**
```python
# Get gyroscope data (requires hardware integration)
pitch, roll, yaw = read_imu_data()

# Adjust self-zone based on tilt
self.self_zone = calculate_zone_for_tilt(pitch, roll)
```

**Option C: Semantic Segmentation**
Instead of geometric zones, use a model that understands "this is MY vehicle":
```python
# Train a classifier on labeled data
is_self_vehicle = self_vehicle_classifier(detection_patch)
if is_self_vehicle:
    ignore_detection()
```

**Related GitHub Issues:**
- #12: False positives on bumpy roads
- #18: Mirror detected as vehicle during turns
- #23: Need camera stabilization

---

## 🟠 **Medium Priority Issues**

### Issue #2: Detection Lag During Fast Motion

**Symptom:**
- Vehicles disappear/reappear when moving fast
- Tracking IDs change frequently
- Velocity calculations inaccurate

**Cause:**
Nearest-neighbor tracking with 100px threshold fails when vehicles move >100px between frames.

At 60 km/h (16.7 m/s) and 30 FPS:
- Frame interval = 33ms
- Distance traveled = 16.7 m/s × 0.033s = 0.55m
- If vehicle appears 200 pixels tall, 0.55m ≈ 150 pixels
- **Exceeds 100px matching threshold!**

**Workaround:**
```python
# Increase matching threshold for highway speeds
self.MAX_MATCHING_DISTANCE = 200  # pixels (was 100)
```

**Proper Solution:**
Implement Kalman filter prediction:
```python
predicted_position = last_position + velocity * dt
# Match to prediction instead of last position
```

---

### Issue #3: Poor Performance in Low Light

**Symptom:**
- Detection accuracy drops to ~40% at night
- No vehicle detection in tunnels
- High false positive rate (shadows detected as vehicles)

**Cause:**
YOLO trained primarily on daylight images.

**Workaround:**
```python
# Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)

clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
l = clahe.apply(l)

enhanced = cv2.merge([l, a, b])
frame = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
```

**Proper Solution:**
- Train YOLO on night-time dataset
- Use infrared camera
- Implement low-light specific model

---

### Issue #4: Opposite Lane False Positives on Curves

**Symptom:**
- Oncoming vehicles not filtered on sharp curves
- System triggers warnings for non-threats

**Cause:**
Current lane detection assumes straight roads:
```python
if center_x > 0.7 * self.width and velocity_x < -5:
    return 'opposite_lane'
```

On curves, opposite lane vehicles appear in same region as same-lane vehicles.

**Workaround:**
Increase velocity threshold:
```python
if center_x > 0.7 * self.width and velocity_x < -10:  # Stricter
    return 'opposite_lane'
```

**Proper Solution:**
Implement actual lane detection:
```python
def detect_lanes(frame):
    edges = cv2.Canny(frame, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50)
    
    # Classify vehicles based on which side of lane line they are
    for vehicle in vehicles:
        if is_on_opposite_side_of_lane_line(vehicle, lines):
            ignore_vehicle()
```

---

## 🟢 **Minor Issues**

### Issue #5: Inconsistent Class Labels

**Symptom:**
- Same vehicle labeled as "car" then "motorbike"
- Detection confidence fluctuates

**Cause:**
- YOLO confidence varies frame-to-frame
- Partial occlusion changes appearance

**Workaround:**
Use most common class over last N frames:
```python
track_history = [2, 2, 3, 2, 2]  # Class IDs over time
most_common = mode(track_history)  # 2 (car)
```

---

### Issue #6: Multiple Bounding Boxes on Large Vehicles

**Symptom:**
- Buses/trucks get multiple detections
- Warning count inflated

**Cause:**
NMS threshold too lenient (0.4 IoU).

**Workaround:**
```python
# More aggressive NMS
indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)  # Was 0.4
```

---

### Issue #7: System Confused by Reflections

**Symptom:**
- Reflections in windows/mirrors detected as vehicles
- Water puddles trigger false alarms

**Cause:**
YOLO doesn't understand context - sees shape, assumes vehicle.

**Workaround:**
Filter detections with very low confidence:
```python
if confidence < 0.6:  # Higher threshold
    ignore_detection()
```

**Proper Solution:**
- Post-processing with context understanding
- Temporal consistency check (reflections flicker)

---

## 🔧 **Performance Issues**

### Issue #8: High CPU Usage (95%+)

**Symptom:**
- Laptop fans run at max
- Battery drains quickly
- System lag

**Cause:**
YOLO inference on CPU is computationally expensive.

**Optimization:**
```python
# 1. Reduce resolution
blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), ...)  # Was 416

# 2. Process every Nth frame
if frame_count % 2 == 0:
    detections = detect_vehicles(frame)
else:
    detections = previous_detections  # Reuse

# 3. Use GPU
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
```

---

## 📊 **Testing Needed**

Issues that need more data:

1. **Rain/Fog Performance**: Untested
2. **Heavy Traffic (20+ vehicles)**: Tracking may fail
3. **Very High Speed (>100 km/h)**: Unknown behavior
4. **Extreme Camera Angles**: May break zone assumptions
5. **Different Vehicle Types**: Tested mostly on cars/bikes

---

## 🐛 **How to Report New Issues**

When reporting bugs, include:

1. **System Info:**
   ```
   OS: Windows 10 / Ubuntu 20.04 / macOS 12
   Python: 3.8.5
   OpenCV: 4.5.3
   CPU/GPU: Intel i5 / NVIDIA GTX 1060
   ```

2. **Steps to Reproduce:**
   ```
   1. Run: python main.py
   2. Choose option 1
   3. Use video: test_highway.mp4
   4. Observe false positive at frame 234
   ```

3. **Expected vs Actual:**
   - Expected: Vehicle ignored (opposite lane)
   - Actual: Critical warning triggered

4. **Screenshots/Videos:**
   Attach frame where issue occurs

5. **Logs:**
   ```python
   # Enable debug logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

---

## 🔗 **Related Documentation**

- [ALGORITHM.md](ALGORITHM.md) - Technical details
- [USAGE.md](USAGE.md) - Configuration guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to fix issues

---

**Last Updated:** October 2024

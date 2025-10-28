import cv2
import numpy as np
import time
import os
from collections import deque

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class VehicleTracker:
    """
    Advanced vehicle tracking with trajectory prediction
    """
    def __init__(self, max_history=10):
        self.tracks = {}  # {track_id: {'positions': deque, 'last_seen': time, 'class': id}}
        self.next_id = 0
        self.max_history = max_history
        self.max_disappeared = 1.0  # seconds before removing track
        
    def update(self, detections, current_time):
        """
        Update tracks with new detections
        Returns: updated tracks with motion vectors
        """
        if len(detections) == 0:
            # Remove old tracks
            self.tracks = {
                tid: track for tid, track in self.tracks.items()
                if current_time - track['last_seen'] < self.max_disappeared
            }
            return []
        
        # Simple nearest-neighbor tracking
        detection_bboxes = [d['bbox'] for d in detections]
        
        if len(self.tracks) == 0:
            # Initialize new tracks
            for det in detections:
                self._create_track(det, current_time)
        else:
            # Match detections to existing tracks
            matched = set()
            
            for tid, track in list(self.tracks.items()):
                if len(track['positions']) == 0:
                    continue
                    
                last_pos = track['positions'][-1]
                last_center = np.array([
                    last_pos[0] + last_pos[2]/2,
                    last_pos[1] + last_pos[3]/2
                ])
                
                # Find closest detection
                min_dist = float('inf')
                best_match = None
                
                for i, det in enumerate(detections):
                    if i in matched:
                        continue
                        
                    bbox = det['bbox']
                    det_center = np.array([
                        bbox[0] + bbox[2]/2,
                        bbox[1] + bbox[3]/2
                    ])
                    
                    dist = np.linalg.norm(last_center - det_center)
                    
                    if dist < min_dist and dist < 100:  # Max matching distance
                        min_dist = dist
                        best_match = i
                
                if best_match is not None:
                    # Update track
                    matched.add(best_match)
                    self._update_track(tid, detections[best_match], current_time)
                elif current_time - track['last_seen'] > self.max_disappeared:
                    # Remove stale track
                    del self.tracks[tid]
            
            # Create tracks for unmatched detections
            for i, det in enumerate(detections):
                if i not in matched:
                    self._create_track(det, current_time)
        
        # Return tracks with motion info
        return self._get_tracked_vehicles()
    
    def _create_track(self, detection, current_time):
        """Create new track"""
        self.tracks[self.next_id] = {
            'positions': deque([detection['bbox']], maxlen=self.max_history),
            'last_seen': current_time,
            'class': detection['class_id'],
            'confidence': detection['confidence']
        }
        self.next_id += 1
    
    def _update_track(self, track_id, detection, current_time):
        """Update existing track"""
        self.tracks[track_id]['positions'].append(detection['bbox'])
        self.tracks[track_id]['last_seen'] = current_time
        self.tracks[track_id]['confidence'] = detection['confidence']
    
    def _get_tracked_vehicles(self):
        """Get all active tracks with motion vectors"""
        tracked = []
        
        for tid, track in self.tracks.items():
            if len(track['positions']) < 2:
                # Not enough history for motion
                tracked.append({
                    'id': tid,
                    'bbox': track['positions'][-1],
                    'class': track['class'],
                    'velocity': (0, 0),
                    'history_length': len(track['positions'])
                })
            else:
                # Calculate velocity
                curr = track['positions'][-1]
                prev = track['positions'][-2]
                
                curr_center = np.array([curr[0] + curr[2]/2, curr[1] + curr[3]/2])
                prev_center = np.array([prev[0] + prev[2]/2, prev[1] + prev[3]/2])
                
                velocity = curr_center - prev_center
                
                tracked.append({
                    'id': tid,
                    'bbox': curr,
                    'class': track['class'],
                    'velocity': tuple(velocity),
                    'history_length': len(track['positions']),
                    'positions': list(track['positions'])
                })
        
        return tracked


class AdaptiveBlindSpotZone:
    """
    Dynamic blind spot zones that adapt to vehicle motion and scene context
    """
    def __init__(self, frame_width, frame_height, side='left'):
        self.width = frame_width
        self.height = frame_height
        self.side = side
        
        # Base zones (static)
        if side == 'left':
            self.base_critical = (0, int(0.35 * frame_width))
            self.base_warning = (int(0.35 * frame_width), int(0.65 * frame_width))
            
            # --- NEW SELF-ZONE (TUNE THESE VALUES) ---
            # Ignore detections in the bottom-right (e.g., mirror)
            # Format: (x_min, y_min, x_max, y_max)
            self.self_zone = (
                int(0.7 * frame_width),  # 70% from left
                int(0.6 * frame_height), # 60% from top
                frame_width,             # Far right
                frame_height             # Bottom
            )
        else:  # right side
            self.base_critical = (int(0.65 * frame_width), frame_width)
            self.base_warning = (int(0.35 * frame_width), int(0.65 * frame_width))
            
            # --- NEW SELF-ZONE (TUNE THESE VALUES) ---
            # Ignore detections in the bottom-left (e.g., mirror)
            self.self_zone = (
                0,                       # Far left
                int(0.6 * frame_height), # 60% from top
                int(0.3 * frame_width),  # 30% from left
                frame_height             # Bottom
            )
        
        # Lane detection parameters
        self.lane_center = frame_width // 2
        self.lane_width = int(0.3 * frame_width)  # Estimated lane width

    def _is_in_self_zone(self, bbox):
        """
        Check if the detection is likely part of the user's own vehicle
        by seeing if its center falls within the defined 'self_zone'.
        (Reverted from overlap check, which was too aggressive)
        """
        x, y, w, h = bbox
        center_x = x + w // 2
        center_y = y + h // 2
        
        sz_x1, sz_y1, sz_x2, sz_y2 = self.self_zone
        
        if (sz_x1 <= center_x <= sz_x2) and (sz_y1 <= center_y <= sz_y2):
            return True
        return False

    def classify_threat(self, tracked_vehicle, frame):
        """
        Advanced threat classification considering:
        - Position in frame
        - Motion direction (approaching/departing)
        - Lateral position (same lane vs opposite)
        - Size (distance proxy)
        """
        bbox = tracked_vehicle['bbox']
        velocity = tracked_vehicle['velocity']
        
        x, y, w, h = bbox
        center_x = x + w // 2
        center_y = y + h // 2
        
        # 1. Self-vehicle exclusion zone filter (NEW FIRST CHECK)
        if self._is_in_self_zone(bbox):
            return 'none', "In self-vehicle zone"
        
        # 2. Vertical position filter (ignore sky/ground)
        if center_y < 0.15 * self.height or center_y > 0.85 * self.height:
            return 'none', "Out of ROI (vertical)"
        
        # 3. Lane position analysis
        lane_status = self._analyze_lane_position(center_x, velocity)
        if lane_status == 'opposite_lane':
            return 'none', "Opposite lane traffic"
        
        # 4. Size-based distance estimation (run this first)
        distance_threat = self._analyze_distance(h)
        
        # 5. Motion analysis
        motion_threat, reason = self._analyze_motion(bbox, velocity)
        
        # 6. Combine threat levels
        
        # Check for distant vehicles first
        if distance_threat == 'safe':
            return 'safe', "Distant vehicle"
            
        # Check for stationary 'self' objects (this is the old check,
        # but the self-zone check above is more robust)
        if motion_threat == 'none':
            return 'none', reason
            
        # If we are here, the vehicle is 'warning' or 'critical' distance
        # AND it is not stationary (not self-bike).
        # Now, we take the worst of the two threats.
        
        if motion_threat == 'critical' or distance_threat == 'critical':
            final_threat = 'critical'
            # Assign the more specific reason
            reason = "Very close" if distance_threat == 'critical' else reason
        elif motion_threat == 'warning' or distance_threat == 'warning':
            final_threat = 'warning'
            reason = "Moderately close" if distance_threat == 'warning' and motion_threat == 'safe' else reason
        else:
            final_threat = 'safe' 
            reason = "No immediate threat"

        return final_threat, reason
    
    def _analyze_lane_position(self, center_x, velocity):
        """
        Determine if vehicle is in same lane or opposite lane
        """
        vx, vy = velocity
        
        if self.side == 'left':
            # For left mirror, vehicles on far right are likely opposite lane
            if center_x > 0.7 * self.width:
                # Check if moving right-to-left (oncoming)
                if vx < -5:  # Moving leftward significantly
                    return 'opposite_lane'
        else:  # right side
            # For right mirror, vehicles on far left are likely opposite lane
            if center_x < 0.3 * self.width:
                # Check if moving left-to-right (oncoming)
                if vx > 5:  # Moving rightward significantly
                    return 'opposite_lane'
        
        return 'same_lane'
    
    def _analyze_motion(self, bbox, velocity):
        """
        Analyze vehicle motion to determine threat level
        """
        x, y, w, h = bbox
        center_x = x + w // 2
        vx, vy = velocity
        
        speed = np.sqrt(vx**2 + vy**2)
        
        # --- 'if speed < 2:' CHECK REMOVED AS REQUESTED ---
        
        # Analyze direction
        if self.side == 'left':
            # For left side: vehicles moving left (negative vx) are approaching
            if vx < -3:  # Approaching from right
                if center_x < self.base_critical[1]:
                    return 'critical', "Fast approach in blind spot"
                elif center_x < self.base_warning[1]:
                    return 'warning', "Approaching blind spot"
            elif vx > 3:  # Moving away
                return 'safe', "Moving away"
            else:  # Parallel motion
                if center_x < self.base_critical[1]:
                    return 'critical', "Parallel in blind spot"
                elif center_x < self.base_warning[1]:
                    return 'warning', "Parallel nearby"
        else:  # right side
            # For right side: vehicles moving right (positive vx) are approaching
            if vx > 3:  # Approaching from left
                if center_x > self.base_critical[0]:
                    return 'critical', "Fast approach in blind spot"
                elif center_x > self.base_warning[0]:
                    return 'warning', "Approaching blind spot"
            elif vx < -3:  # Moving away
                return 'safe', "Moving away"
            else:  # Parallel motion
                if center_x > self.base_critical[0]:
                    return 'critical', "Parallel in blind spot"
                elif center_x > self.base_warning[0]:
                    return 'warning', "Parallel nearby"
        
        return 'safe', "No immediate threat"
    
    def _analyze_distance(self, bbox_height):
        """
        Use bounding box height as distance proxy
        Larger boxes = closer vehicles = higher threat
        """
        height_ratio = bbox_height / self.height
        
        # --- Using stricter values ---
        if height_ratio > 0.45:  # Very close (Original was 0.4)
            return 'critical'
        elif height_ratio > 0.3:  # Moderately close (Original was 0.25)
            return 'warning'
        else:
            return 'safe'
    
    def draw_zones(self, frame):
        """Draw adaptive zones"""
        overlay = frame.copy()
        
        # Draw semi-transparent zone regions
        if self.side == 'left':
            cv2.rectangle(overlay, 
                         (self.base_critical[0], int(0.15 * self.height)),
                         (self.base_critical[1], int(0.85 * self.height)),
                         (0, 0, 200), -1)
            cv2.rectangle(overlay, 
                         (self.base_warning[0], int(0.15 * self.height)),
                         (self.base_warning[1], int(0.85 * self.height)),
                         (0, 150, 200), -1)
        else:
            cv2.rectangle(overlay, 
                         (self.base_critical[0], int(0.15 * self.height)),
                         (self.base_critical[1], int(0.85 * self.height)),
                         (0, 0, 200), -1)
            cv2.rectangle(overlay, 
                         (self.base_warning[0], int(0.15 * self.height)),
                         (self.base_warning[1], int(0.85 * self.height)),
                         (0, 150, 200), -1)
        
        # --- NEW: Draw self-zone overlay ---
        sz_x1, sz_y1, sz_x2, sz_y2 = self.self_zone
        cv2.rectangle(overlay, (sz_x1, sz_y1), (sz_x2, sz_y2), (200, 0, 0), -1) # Blue
        
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
        
        # Draw zone boundaries
        if self.side == 'left':
            cv2.line(frame, (self.base_critical[1], 0),
                    (self.base_critical[1], self.height), (0, 0, 255), 2)
            cv2.line(frame, (self.base_warning[1], 0),
                    (self.base_warning[1], self.height), (0, 165, 255), 2)
            
            cv2.putText(frame, "CRITICAL ZONE", (10, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.line(frame, (self.base_critical[0], 0),
                    (self.base_critical[0], self.height), (0, 0, 255), 2)
            cv2.line(frame, (self.base_warning[0], 0),
                    (self.base_warning[0], self.height), (0, 165, 255), 2)
            
            cv2.putText(frame, "CRITICAL ZONE", (int(0.7 * self.width), 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # --- NEW: Draw self-zone text ---
        cv2.putText(frame, "SELF-ZONE", (sz_x1 + 5, sz_y1 + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame


class AdvancedBlindSpotDetection:
    """
    Production-grade blind spot detection with motion analysis
    """
    def __init__(self):
        # Check model files
        if not os.path.exists("yolov3.weights"):
            print("❌ ERROR: yolov3.weights not found!")
            exit(1)
        
        print("Loading AI model...")
        self.net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
        
        with open("coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        
        layer_names = self.net.getLayerNames()
        try:
            unconnected = self.net.getUnconnectedOutLayers()
            if isinstance(unconnected, np.ndarray):
                if unconnected.ndim == 1:
                    self.output_layers = [layer_names[i - 1] for i in unconnected]
                else:
                    self.output_layers = [layer_names[i[0] - 1] for i in unconnected]
        except:
            self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        
        self.vehicle_classes = [1, 2, 3, 5, 7]  # bicycle, car, motorbike, bus, truck
        
        # Initialize trackers for each side
        self.trackers = {'left': VehicleTracker(), 'right': VehicleTracker()}
        
        # Audio
        self.warning_sound = None
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                if os.path.exists("sounds/warning_beep.wav"):
                    self.warning_sound = pygame.mixer.Sound("sounds/warning_beep.wav")
            except:
                pass
        
        self.last_warning_time = {'left': 0, 'right': 0}
        self.warning_cooldown = 1.5
        
        print("✓ Advanced detection system initialized")
    
    def detect_vehicles(self, frame):
        """Basic YOLO detection"""
        height, width = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)
        
        detections = []
        
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5 and class_id in self.vehicle_classes:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    detections.append({
                        'bbox': [x, y, w, h],
                        'confidence': float(confidence),
                        'class_id': class_id
                    })
        
        # Apply NMS
        if len(detections) > 0:
            boxes = [d['bbox'] for d in detections]
            confidences = [d['confidence'] for d in detections]
            
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            
            if len(indexes) > 0:
                if isinstance(indexes, tuple):
                    indexes = indexes[0]
                indexes = indexes.flatten() if hasattr(indexes, 'flatten') else indexes
                detections = [detections[i] for i in indexes]
            else:
                detections = []
        
        return detections
    
    def process_side_view(self, frame, side, adaptive_zone):
        """Process with motion tracking"""
        current_time = time.time()
        
        # Detect vehicles
        detections = self.detect_vehicles(frame)
        
        # Update tracker
        tracked_vehicles = self.trackers[side].update(detections, current_time)
        
        # Draw zones
        frame = adaptive_zone.draw_zones(frame)
        
        # Analyze each tracked vehicle
        critical_detected = False
        warning_detected = False
        threat_vehicles = []
        
        for vehicle in tracked_vehicles:
            threat_level, reason = adaptive_zone.classify_threat(vehicle, frame)
            
            if threat_level == 'none':
                continue
            
            threat_vehicles.append({
                'vehicle': vehicle,
                'threat': threat_level,
                'reason': reason
            })
            
            if threat_level == 'critical':
                critical_detected = True
            elif threat_level == 'warning':
                warning_detected = True
        
        # Draw detections with motion vectors
        for tv in threat_vehicles:
            vehicle = tv['vehicle']
            threat = tv['threat']
            reason = tv['reason']
            
            bbox = vehicle['bbox']
            x, y, w, h = bbox
            
            # Color by threat
            if threat == 'critical':
                color = (0, 0, 255)
                thickness = 3
            elif threat == 'warning':
                color = (0, 165, 255)
                thickness = 2
            else:
                color = (0, 255, 0)
                thickness = 2
            
            # Draw box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
            
            # Draw motion vector
            vx, vy = vehicle['velocity']
            center = (x + w//2, y + h//2)
            end_point = (int(center[0] + vx * 3), int(center[1] + vy * 3))
            cv2.arrowedLine(frame, center, end_point, color, 2, tipLength=0.3)
            
            # Labels
            label = self.classes[vehicle['class']]
            cv2.putText(frame, f"{label.upper()}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.putText(frame, f"[{threat.upper()}]", (x, y + h + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Speed indicator
            speed = np.sqrt(vx**2 + vy**2)
            cv2.putText(frame, f"Speed: {speed:.1f}px/f", (x, y + h + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Trigger warnings
        if critical_detected and (current_time - self.last_warning_time[side]) > self.warning_cooldown:
            self.trigger_warning(frame, side, "CRITICAL")
            self.last_warning_time[side] = current_time
        elif warning_detected and (current_time - self.last_warning_time[side]) > self.warning_cooldown:
            self.trigger_warning(frame, side, "WARNING")
            self.last_warning_time[side] = current_time
        
        # Status display
        if critical_detected:
            status = f"⚠️ CRITICAL - {len([t for t in threat_vehicles if t['threat']=='critical'])} THREATS"
            status_color = (0, 0, 255)
        elif warning_detected:
            status = f"⚡ WARNING - {len([t for t in threat_vehicles if t['threat']=='warning'])} VEHICLES"
            status_color = (0, 165, 255)
        else:
            status = "✓ CLEAR"
            status_color = (0, 255, 0)
        
        cv2.putText(frame, status, (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Tracking info
        cv2.putText(frame, f"Tracked: {len(tracked_vehicles)}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame, critical_detected, warning_detected
    
    def trigger_warning(self, frame, side, level):
        """Visual + audio warning"""
        height, width = frame.shape[:2]
        overlay = frame.copy()
        
        if level == "CRITICAL":
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 255), 20)
        else:
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 165, 255), 15)
        
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        if self.warning_sound:
            try:
                self.warning_sound.play()
            except:
                pass
    
    def process_single_camera(self, video_path, side, output_path=None):
        """Process single side"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"❌ Error: Cannot open {video_path}")
            return
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Processing {side} side: {width}x{height} @ {fps} FPS")
        
        adaptive_zone = AdaptiveBlindSpotZone(width, height, side)
        
        out = None
        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                processed_frame, critical, warning = self.process_side_view(
                    frame, side, adaptive_zone)
                
                cv2.imshow(f'{side.upper()} - Advanced Blind Spot Detection', processed_frame)
                
                if out:
                    out.write(processed_frame)
                
                frame_count += 1
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            if out:
                out.release()
            cv2.destroyAllWindows()
        
        print(f"✓ Processed {frame_count} frames")


# Main execution
if __name__ == "__main__":
    print("="*60)
    print("  🏍️ ADVANCED BLIND SPOT DETECTION v2.0")
    print("  Features: Motion Tracking | Trajectory Prediction")
    print("="*60)
    
    try:
        detector = AdvancedBlindSpotDetection()
        
        print("\nSelect Mode:")
        print("1. Single Camera (Left side)")
        print("2. Single Camera (Right side)")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice in ["1", "2"]:
            side = "left" if choice == "1" else "right"
            video_path = input(f"Enter {side} video path: ").strip()
            
            if os.path.exists(video_path):
                detector.process_single_camera(video_path, side, f"output/{side}_advanced.mp4")
            else:
                print(f"❌ File not found: {video_path}")
        elif choice == "3":
            print("Exiting...")
        else:
            print("Invalid choice!")
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if PYGAME_AVAILABLE:
            pygame.mixer.quit()
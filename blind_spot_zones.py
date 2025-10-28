import numpy as np

class BlindSpotZone:
    """
    Defines and manages blind spot zones for 2-wheelers
    """
    def __init__(self, frame_width, frame_height, side='left'):
        self.width = frame_width
        self.height = frame_height
        self.side = side
        
        # Define zones (as percentage of frame)
        # Zone 1: Critical blind spot (60-100% from edge)
        # Zone 2: Warning zone (30-60% from edge)
        # Zone 3: Safe zone (0-30% from edge)
        
        if side == 'left':
            self.critical_zone = (0, int(0.4 * frame_width))
            self.warning_zone = (int(0.4 * frame_width), int(0.7 * frame_width))
            self.safe_zone = (int(0.7 * frame_width), frame_width)
        else:  # right
            self.critical_zone = (int(0.6 * frame_width), frame_width)
            self.warning_zone = (int(0.3 * frame_width), int(0.6 * frame_width))
            self.safe_zone = (0, int(0.3 * frame_width))
    
    def get_zone(self, bbox):
        """
        Determine which zone a bounding box is in
        Returns: 'critical', 'warning', 'safe', or 'none'
        """
        x, y, w, h = bbox
        center_x = x + w // 2
        
        # Check if vehicle is in relevant vertical area (middle 60% of frame)
        if y < 0.2 * self.height or y > 0.8 * self.height:
            return 'none'
        
        if self.side == 'left':
            if center_x <= self.critical_zone[1]:
                return 'critical'
            elif center_x <= self.warning_zone[1]:
                return 'warning'
            else:
                return 'safe'
        else:  # right
            if center_x >= self.critical_zone[0]:
                return 'critical'
            elif center_x >= self.warning_zone[0]:
                return 'warning'
            else:
                return 'safe'
    
    def draw_zones(self, frame):
        """Draw zone boundaries on frame for visualization"""
        import cv2
        
        # Draw zone lines
        if self.side == 'left':
            cv2.line(frame, (self.critical_zone[1], 0), 
                    (self.critical_zone[1], self.height), (0, 0, 255), 2)
            cv2.line(frame, (self.warning_zone[1], 0), 
                    (self.warning_zone[1], self.height), (0, 165, 255), 2)
            
            # Labels
            cv2.putText(frame, "CRITICAL", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "WARNING", (int(0.45 * self.width), 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        else:
            cv2.line(frame, (self.critical_zone[0], 0), 
                    (self.critical_zone[0], self.height), (0, 0, 255), 2)
            cv2.line(frame, (self.warning_zone[0], 0), 
                    (self.warning_zone[0], self.height), (0, 165, 255), 2)
            
            cv2.putText(frame, "CRITICAL", (int(0.65 * self.width), 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "WARNING", (int(0.35 * self.width), 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        
        return frame
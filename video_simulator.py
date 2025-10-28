# video_simulator.py
import cv2
import os

def create_side_view_simulation(input_video, output_left, output_right):
    """
    Simulate left/right side views from a single front dashcam video
    This splits the video horizontally to create two side views
    """
    print(f"\n🎬 Processing: {input_video}")
    
    cap = cv2.VideoCapture(input_video)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open video file: {input_video}")
        return False
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video Info:")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   Total Frames: {total_frames}")
    
    # Create output folder if it doesn't exist
    os.makedirs("videos", exist_ok=True)
    
    # Calculate crop width (we'll use half the video width for each side)
    crop_width = width // 2
    
    # Create video writers
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_left = cv2.VideoWriter(output_left, fourcc, fps, (crop_width, height))
    out_right = cv2.VideoWriter(output_right, fourcc, fps, (crop_width, height))
    
    if not out_left.isOpened() or not out_right.isOpened():
        print("❌ Error: Cannot create output video files")
        return False
    
    frame_count = 0
    print(f"\n⚙️ Processing frames...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Split frame into left and right halves
        left_frame = frame[:, :crop_width]  # Left half of frame
        right_frame = frame[:, crop_width:]  # Right half of frame
        
        # Optional: Flip right frame to simulate mirror view
        # right_frame = cv2.flip(right_frame, 1)
        
        # Write frames
        out_left.write(left_frame)
        out_right.write(right_frame)
        
        frame_count += 1
        
        # Show progress every 30 frames
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"   Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)", end='\r')
    
    # Cleanup
    cap.release()
    out_left.release()
    out_right.release()
    
    print(f"\n\n✅ Conversion Complete!")
    print(f"   Processed {frame_count} frames")
    print(f"   Left view saved: {output_left}")
    print(f"   Right view saved: {output_right}")
    print("="*60)
    
    return True

def process_all_videos():
    """Process all dashcam videos in the videos folder"""
    print("="*60)
    print("  🎥 DASHCAM TO SIDE-VIEW CONVERTER")
    print("="*60)
    
    # Create videos folder if doesn't exist
    os.makedirs("videos", exist_ok=True)
    
    print("\n📂 Available video files:")
    print("   Place your GoPro/dashcam videos in the 'videos' folder")
    print("   with names like: dashcam1.mp4, dashcam2.mp4, etc.\n")
    
    # Manual file input
    print("Enter the name of your dashcam video file")
    print("(should be in the 'videos' folder)")
    video_name = input("Video filename (e.g., dashcam.mp4): ").strip()
    
    input_path = f"videos/{video_name}"
    
    # Check if file exists
    if not os.path.exists(input_path):
        print(f"\n❌ Error: File not found: {input_path}")
        print("   Make sure the video is in the 'videos' folder!")
        return
    
    # Generate output names
    base_name = os.path.splitext(video_name)[0]
    output_left = f"videos/{base_name}_left.mp4"
    output_right = f"videos/{base_name}_right.mp4"
    
    # Process
    success = create_side_view_simulation(input_path, output_left, output_right)
    
    if success:
        print(f"\n🎯 Next Steps:")
        print(f"   1. Check the generated files:")
        print(f"      - {output_left}")
        print(f"      - {output_right}")
        print(f"   2. Update main.py to use these filenames")
        print(f"   3. Run: python main.py")

if __name__ == "__main__":
    process_all_videos()
# Project Screenshots

Place your screenshots here with these names:

## Required Screenshots

1. **right_side_safe.png** - Vehicle in safe zone (right mirror view)
   - From your Image 1
   - Shows: Car far away, green box, SAFE status

2. **left_side_critical.png** - Critical warning scenario (left mirror view)
   - From your Image 2
   - Shows: Motorcycle in critical zone, red border, CRITICAL warning

3. **multi_vehicle_tracking.png** - Multiple vehicles being tracked
   - From your Image 3 or 5
   - Shows: Truck + Auto-rickshaw with separate tracking IDs

4. **motion_vectors.png** - Arrows showing vehicle movement
   - Any image showing green arrows
   - Demonstrates velocity tracking

5. **self_zone_demo.png** - Self-zone filtering in action
   - Shows blue SELF-ZONE overlay
   - Demonstrates own vehicle parts being ignored

## How to Add

1. Take screenshots from your processed video
2. Save with exact names above
3. Place in this folder
4. Commit to git:
   ```bash
   git add docs/images/*.png
   git commit -m "docs: Add system screenshots"
   ```

## Image Guidelines

- **Format**: PNG (transparent background preferred)
- **Size**: 800-1200px width (for GitHub display)
- **Quality**: High enough to see text labels clearly
- **Compression**: Use TinyPNG or similar to reduce file size

## Current Status

Based on your images:
- ✅ Image 1 → right_side_safe.png
- ✅ Image 2 → left_side_critical.png  
- ✅ Image 3 → multi_vehicle_tracking.png
- ✅ Image 4 → motion_vectors.png (with blur)
- ✅ Image 5 → multi_vehicle_tracking_alt.png

Save your 5 images with appropriate names and they'll appear in the README automatically!

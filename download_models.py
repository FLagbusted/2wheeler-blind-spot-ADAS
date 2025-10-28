"""
YOLO Model Downloader
Downloads YOLOv3 weights and configuration files
"""
import urllib.request
import os
import sys

def download_file(url, filename):
    """Download file with progress bar"""
    print(f"\nDownloading {filename}...")
    print(f"URL: {url}")
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100.0 / total_size, 100)
        
        bar_length = 50
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        sys.stdout.write(f'\r[{bar}] {percent:.1f}% ({downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB)')
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        print(f"\n✓ {filename} downloaded successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error downloading {filename}: {e}")
        return False

def main():
    print("="*60)
    print("  YOLO MODEL DOWNLOADER")
    print("="*60)
    print("\nThis will download:")
    print("  1. yolov3.weights (237 MB)")
    print("  2. yolov3.cfg (8 KB)")
    print("  3. coco.names (1 KB)")
    print("\nTotal download size: ~237 MB")
    print("="*60)
    
    response = input("\nProceed with download? (y/n): ").strip().lower()
    if response != 'y':
        print("Download cancelled.")
        return
    
    files = [
        {
            'url': 'https://pjreddie.com/media/files/yolov3.weights',
            'filename': 'yolov3.weights',
            'size': '237 MB'
        },
        {
            'url': 'https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg',
            'filename': 'yolov3.cfg',
            'size': '8 KB'
        },
        {
            'url': 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names',
            'filename': 'coco.names',
            'size': '1 KB'
        }
    ]
    
    success_count = 0
    
    for file_info in files:
        # Check if file already exists
        if os.path.exists(file_info['filename']):
            print(f"\n⚠ {file_info['filename']} already exists")
            overwrite = input(f"  Overwrite? (y/n): ").strip().lower()
            if overwrite != 'y':
                print(f"  Skipping {file_info['filename']}")
                success_count += 1
                continue
        
        # Download file
        if download_file(file_info['url'], file_info['filename']):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == len(files):
        print("✓ All files downloaded successfully!")
        print("\nNext steps:")
        print("  1. Run: python sound_generator.py")
        print("  2. Run: python main.py")
    else:
        print(f"⚠ {success_count}/{len(files)} files downloaded")
        print("\nMissing files must be downloaded manually from:")
        for file_info in files:
            if not os.path.exists(file_info['filename']):
                print(f"  {file_info['url']}")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

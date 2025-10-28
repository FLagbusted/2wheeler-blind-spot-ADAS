# sound_generator.py
import numpy as np
import wave

def generate_warning_beep():
    """Generate a warning beep sound"""
    sample_rate = 44100
    duration = 0.3  # seconds
    frequency = 1000  # Hz
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * frequency * t)
    
    # Add envelope to avoid clicks
    envelope = np.exp(-3 * t)
    audio = audio * envelope
    
    # Convert to 16-bit
    audio = (audio * 32767).astype(np.int16)
    
    # Save
    with wave.open("sounds/warning_beep.wav", "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())
    
    print("✓ Warning sound generated: sounds/warning_beep.wav")

if __name__ == "__main__":
    import os
    os.makedirs("sounds", exist_ok=True)
    generate_warning_beep()
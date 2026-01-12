from audio.generator import AudioGenerator
from audio.analyzer import AudioAnalyzer
from audio.player import AudioPlayer
import time
import os
import numpy as np
from PIL import Image

def run_test():
    img_name = "demo-test.png"
    if not os.path.exists(img_name):
        print(f"Creating dummy {img_name} because you didn't have one...")
        # create a simple gradient image for testing
        arr = np.linspace(0, 255, 100*100).reshape((100, 100)).astype(np.uint8)
        img = Image.fromarray(arr)
        img.save(img_name)

    print("\n--- 1. Testing Generator ---")
    gen = AudioGenerator()

    # generating 2 seconds to keep it quick 
    gen.generate(img_name, duration_seconds=2.0, iterations=8)
    
    if not os.path.exists("output.wav"):
        print("FAIL: output.wav was not created.")
        return
    print("PASS: Audio generated.")

    print("\n--- 2. Testing Analyzer ---")
    analyzer = AudioAnalyzer()
    success, filename, sr, duration = analyzer.load_file("output.wav")
    
    if success:
        print(f"PASS: Loaded {filename}")
        print(f"Stats: {sr}Hz | {duration:.2f} seconds")
        
        # Check if math happened
        spectrogram, _ = analyzer.get_spectrogram_data()
        if spectrogram is not None:
            print(f"PASS: Spectrogram calculated (Shape: {spectrogram.shape})")
        else:
            print("FAIL: Spectrogram is empty.")
    else:
        print("FAIL: Could not load file.")
        return

    # player
    print("\n--- 3. Testing Player ---")
    player = AudioPlayer()
    
    print("Playing via Pygame (File)...")
    player.play_file("output.wav")
    
    # Simple loop to wait while playing
    while player.is_file_playing():
        time.sleep(0.1)
    
    print("PASS: Playback finished.")
    
    #Test Raw Data Playback
    print("Playing via SoundDevice (Raw Array)...")
    raw_data = analyzer.get_audio_data()
    player.play_array(raw_data, sr)
    print("PASS: Raw playback finished.")

if __name__ == "__main__":
    run_test()
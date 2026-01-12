import matplotlib.pyplot as plt
import librosa.display
import os
from audio.analyzer import AudioAnalyzer
from audio.generator import AudioGenerator

def run_visual_test():
    target_file = "output-test2.wav"
    
    if not os.path.exists(target_file):
        print("No audio found, generating some noise from demo-test.png...")
        gen = AudioGenerator()
        if os.path.exists("demo-test.png"):
            gen.generate("demo-test.png")
        else:
            print("Error: No image and no audio. Run test_logic.py first.")
            return

    print(f"Analyzing {target_file}...")

    # initialize our analyzer logic
    analyzer = AudioAnalyzer()
    
    # load the file
    success, filename, sr, duration = analyzer.load_file(target_file)
    
    if not success:
        print("Failed to load audio.")
        return

    # get the math matrix (spectrogram)
    # S_db is the loudness in decibels
    S_db, sr = analyzer.get_spectrogram_data()

    print("Plotting spectrogram...")

    # setup the plot figure
    plt.figure(figsize=(10, 4))
    
    # use librosa function to draw the heatmap
    # y_axis='hz' shows frequency in Hz
    # x_axis='time' shows time in sec(s)
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz')
    
    plt.colorbar(format='%+2.0f dB')
    plt.title(f"Spectrogram of {filename}")
    plt.tight_layout()
    
    # show
    print("Check the popup window!")
    plt.show()

if __name__ == "__main__":
    run_visual_test()
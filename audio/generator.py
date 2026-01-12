import numpy as np
import soundfile as sf
from PIL import Image
import librosa

from config import SAMPLE_RATE, N_FFT, HOP_LENGTH, OUTPUT_FILENAME

class AudioGenerator:
    def generate(self, image_path, duration_seconds=3.0, iterations=32):
        """
        .Load the image.
        .Resizes it to match the requested audio duration.
        .Performs Inverse FFT to turn pixels into sound.
        .Saves the file.
        """
        # I am becoming obsessed with the try:except block
        try:
            print(f"--- Loading Image: {image_path} ---")
            
            # Load and convert to Grayscale
            original_img = Image.open(image_path).convert('L')
            
            # dimensions needed for audio math

            frames_needed = int((duration_seconds * SAMPLE_RATE) / HOP_LENGTH)
            # Height = Frequency Bins (1025 for n_fft=2048)

            freq_bins = int(N_FFT / 2) + 1
            
            print(f"Resizing image to: {frames_needed}x{freq_bins} pixels")
            
            #Resize image to fit audio dimensions (BICUBIC is much smooth)
            resized_img = original_img.resize((frames_needed, freq_bins), Image.Resampling.BICUBIC)
            
            # then we flip the image
            # Because in images; (0,0) is Top-Left and in Audio; (0,0) is Bottom-Left (Low Freq). 
            # I was having issues with the audio being flipped.

            resized_img = resized_img.transpose(Image.FLIP_TOP_BOTTOM)
            
            #Convert pixels (0-255) to Audio Magnitude (0.0-1.0)so as to normalize the audio.
            spectrogram = np.asarray(resized_img).astype(np.float32) / 255.0
            
            #Apply some contrast (Cube the values) why do we do this?
             # This makes the black background truly silent and lines clearer
            spectrogram = np.power(spectrogram, 3) * 100

            # We use Griffin-Lim Algorithm that was something I just encountered becuase of this audio generator project.
            # Converts Spectrogram (Frequency Map) -> Waveform (Audio)
            print("Computing Inverse FFT (wait for it, or else!)...")
            audio_signal = librosa.griffinlim(
                spectrogram, 
                n_iter=iterations, 
                hop_length=HOP_LENGTH, 
                n_fft=N_FFT
            )

            sf.write(OUTPUT_FILENAME, audio_signal, SAMPLE_RATE)
            print(f"Success! Saved to {OUTPUT_FILENAME}")
            
        except Exception as e:
            print(f"Error: {e}")

            # i gotta go play no man's sky,..... hehe


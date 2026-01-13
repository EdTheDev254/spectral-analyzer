import numpy as np
import soundfile as sf
from PIL import Image
import librosa

from config import SAMPLE_RATE, N_FFT, HOP_LENGTH, OUTPUT_FILENAME

class AudioGenerator:
    def generate_from_image(self, pil_image, duration_seconds=3.0, iterations=32):
        """
        Takes a PIL Image object directly (from the painter tab),
        converts it to audio, and saves it.
        """
        # I am becoming obsessed with the try:except block
        try:
            print(f"--- Generating Audio ({duration_seconds}s) ---")
            
            # We don't need Image.open() here because we received the image object directly
            # Just ensure it is grayscale
            original_img = pil_image.convert('L')
            
            # dimensions needed for audio math
            frames_needed = int((duration_seconds * SAMPLE_RATE) / HOP_LENGTH)
            
            # Height = Frequency Bins (1025 for n_fft=2048)
            freq_bins = int(N_FFT / 2) + 1
            
            print(f"Resizing internal image to: {frames_needed}x{freq_bins}")
            
            # Resize image to fit audio dimensions (BICUBIC is much smooth)
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
            
            return OUTPUT_FILENAME, audio_signal
            
        except Exception as e:
            print(f"Error: {e}")

            return None, None

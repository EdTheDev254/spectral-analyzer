import numpy as np
import soundfile as sf
from PIL import Image
import librosa

from config import SAMPLE_RATE, N_FFT, HOP_LENGTH, OUTPUT_FILENAME

class AudioGenerator:
    def generate_from_image(self, pil_image, duration_seconds=3.0, iterations=32, output_path=None, pitch_shift=0, sample_rate=None):
        """
        Takes a PIL Image object directly (from the painter tab),
        converts it to audio, and saves it.
        pitch_shift: Semitones to shift pitch (-12 to +12)
        sample_rate: Target sample rate (uses config default if None)
        """
        # I am becoming obsessed with the try:except block
        try:
            if sample_rate is None:
                sample_rate = SAMPLE_RATE
            
            print(f"--- Generating Audio ({duration_seconds}s) at {sample_rate}Hz ---")
            
            # We don't need Image.open() here because we received the image object directly
            # Just ensure it is grayscale
            original_img = pil_image.convert('L')
            
            # dimensions needed for audio math
            frames_needed = int((duration_seconds * sample_rate) / HOP_LENGTH)
            
            # Height = Frequency Bins (1025 for n_fft=2048)
            freq_bins = int(N_FFT / 2) + 1
            
            print(f"Resizing internal image to: {frames_needed}x{freq_bins}")
            
            # Resize image to fit audio dimensions (BICUBIC is much smooth)
            # Use LANCZOS here because it handles the "stretching" of long audio better than Bicubic
            resized_img = original_img.resize((frames_needed, freq_bins), Image.Resampling.LANCZOS)
            
            # then we flip the image
            # Because in images; (0,0) is Top-Left and in Audio; (0,0) is Bottom-Left (Low Freq). 
            # I was having issues with the audio being flipped.

            resized_img = resized_img.transpose(Image.FLIP_TOP_BOTTOM)
            
            #Convert pixels (0-255) to Audio Magnitude (0.0-1.0)so as to normalize the audio.
            spectrogram = np.asarray(resized_img).astype(np.float32) / 255.0
            
            # Apply Pitch Shift
            if pitch_shift != 0:
                # Convert semitones to frequency ratio: 2^(semitones/12)
                pitch_ratio = 2 ** (pitch_shift / 12.0)
                
                # Resize vertically (frequency axis)
                # Shift UP = smaller height (compress), Shift DOWN = larger height (expand)
                original_height = spectrogram.shape[0]
                new_height = int(original_height / pitch_ratio)
                
                # Resize using PIL for better quality
                temp_img = Image.fromarray((spectrogram * 255).astype(np.uint8))
                temp_img = temp_img.resize((spectrogram.shape[1], new_height), Image.Resampling.LANCZOS)
                shifted = np.asarray(temp_img).astype(np.float32) / 255.0
                
                # Crop or pad to original height
                if new_height > original_height:
                    # Shifted down, crop from top
                    spectrogram = shifted[:original_height, :]
                else:
                    # Shifted up, pad bottom with zeros
                    spectrogram = np.zeros((original_height, spectrogram.shape[1]), dtype=np.float32)
                    spectrogram[:new_height, :] = shifted
            
            #Apply some contrast (Cube the values) why do we do this?
             # This makes the black background truly silent and lines clearer
            # Changed to 4 to remove the "blur" noise from stretching longer audio
            spectrogram = np.power(spectrogram, 4) * 100

            # We use Griffin-Lim Algorithm that was something I just encountered becuase of this audio generator project.
            # Converts Spectrogram (Frequency Map) -> Waveform (Audio)
            print("Computing Inverse FFT (wait for it, or else!)...")
            audio_signal = librosa.griffinlim(
                spectrogram, 
                n_iter=iterations, 
                hop_length=HOP_LENGTH, 
                n_fft=N_FFT
            )

            target_file = output_path if output_path else OUTPUT_FILENAME
            sf.write(target_file, audio_signal, sample_rate)
            print(f"Success! Saved to {target_file}")
            
            return target_file, audio_signal
            
        except Exception as e:
            print(f"Error: {e}")

            return None, None
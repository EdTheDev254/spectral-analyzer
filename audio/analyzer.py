import librosa
import numpy as np
import os
from config import N_FFT, HOP_LENGTH, HOP_LENGTH_HD

class AudioAnalyzer:
    def __init__(self):
        self.audio_data = None
        self.sr = None
        self.S_db = None # this will hold the spectrogram data

    def load_file(self, file_path):
        # load the audio file
        try:
            # load audio with original sample rate
            self.audio_data, self.sr = librosa.load(file_path, sr=None)
            
            duration = len(self.audio_data) / self.sr
            
            # calculate the spectrogram right away so its ready
            self._compute_spectrogram()
            
            filename = os.path.basename(file_path)
            return True, filename, self.sr, duration
        except Exception as e:
            print(f"Analyzer Load Error: {e}")
            return False, str(e), 0, 0

    def _compute_spectrogram(self):
        # this does the heavy math lifting
        if self.audio_data is None:
            return

        # STFT breaks the audio into frequencies
        D = librosa.stft(self.audio_data, n_fft=N_FFT, hop_length=HOP_LENGTH)
        
        # convert to absolute values aka magnitude and then to decibels
        # we use decibels cause human hearing is logarithmic
        self.S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

    
    def recompute_spectrogram(self, high_res=False):
        # recalculate the math with different resolution settings
        if self.audio_data is None:
            return

        # choose the hop length based on the setting
        from config import HOP_LENGTH, HOP_LENGTH_HD
        target_hop = HOP_LENGTH_HD if high_res else HOP_LENGTH
        
        # run the STFT math again
        D = librosa.stft(self.audio_data, n_fft=N_FFT, hop_length=target_hop)
        self.S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        
        return target_hop

    def get_spectrogram_data(self):
        return self.S_db, self.sr

    def get_audio_data(self):
        return self.audio_data
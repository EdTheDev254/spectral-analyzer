import pygame
import sounddevice as sd

class AudioPlayer:
    def __init__(self):
        # pre_init helps reduce the delay when you press play
        try:
            pygame.mixer.pre_init(44100, -16, 2, 4096)
            pygame.mixer.init()
            pygame.init()
        except Exception as e:
            print(f"Audio Driver Error: {e}")
            pygame.mixer.init()

    def play_file(self, filename):
        # plays a wav file 
        if filename:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

    def stop_file(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload() #for unloading the file when it is finished

    def is_file_playing(self):
        return pygame.mixer.music.get_busy()

    def play_array(self, audio_data, sample_rate, start_sample=0):
        # plays raw data
        try:
            # play from the specific point in the data
            sd.play(audio_data[start_sample:], sample_rate)
            sd.wait() # wait for it to finish
        except Exception as e:
            print(f"SoundDevice Error: {e}")

    def stop_array(self):
        sd.stop()
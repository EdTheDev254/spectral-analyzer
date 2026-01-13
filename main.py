from audio.generator import AudioGenerator
from ui.main_window import SpectralStudio
import os
"""
if __name__ == "__main__":
    gen = AudioGenerator() # initialize the generator

    my_image = "demo-test.png" 

    if os.path.exists(my_image):
        gen.generate(image_path=my_image, duration_seconds=5.0, iterations=64) # you can change the values if you want
    else:
        print(f"Please place an image named '{my_image}' in this folder to test the generator.")
"""



if __name__ == "__main__":
    app = SpectralStudio()
    
    # handle the X button properly
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    app.mainloop()


# side not, use 3 seconds audio because you will be dividing the image pixels by 3
# since it is 600x600 pixels() you will get a much crisper spectrogram audio using the visualizer
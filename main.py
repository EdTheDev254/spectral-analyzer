from audio.generator import AudioGenerator
import os

if __name__ == "__main__":
    gen = AudioGenerator() # initialize the generator

    my_image = "demo-test.png" 

    if os.path.exists(my_image):
        gen.generate(image_path=my_image, duration_seconds=5.0, iterations=16) # you can change the values if you want
    else:
        print(f"Please place an image named '{my_image}' in this folder to test the generator.")
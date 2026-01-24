# Spectral-Analyzer
I know some great developers have already built audio spectral viewers, but I wanna build one step by step....

# How to run it

```
python main.py 

```

# Sample

## Original Image
![Alt Text](car.jpg)

## Source Audio
[Listen Audio](output-test2.wav)

## Spectogram View(Viridis)
![Alt Text](test.png)

The original Beetle photo was converted to audio by mapping pixel brightness to frequencies. Each part of the image produces sound at different frequencies over time. The audio was then analyzed as a spectrogram using the same program, which shows frequency on the vertical axis and time on the horizontal axis. Since the image data was encoded as frequencies, viewing them in a spectrogram shows the Beetle's shape again.(it is not perfect, but it can be seen)

# Update: New Tabs
It has two new tabs: 
1. Painter Tab - for loading images/ drawing on the canvas and generating audio from it
2. Analyzer Tab - for loading audio files and visualizing them as spectrograms / and can save the spectrogram as an image strip based on the audio length.


![Sample Image](RR_44100Hz_3.8s.png)

you can test this image to audio conversion by uploading the image to the painter tab and clicking on generate audio. 
Sample rate for the audio is 44100 and the duration is 3.8 seconds.





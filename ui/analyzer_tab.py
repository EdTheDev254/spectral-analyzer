import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import librosa.display

from audio.analyzer import AudioAnalyzer
from audio.player import AudioPlayer
from config import COLOR_BG, WINDOW_SIZE, HOP_LENGTH

class AnalyzerTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.analyzer = AudioAnalyzer()
        self.player = AudioPlayer()

        self.is_playing = False
        self.start_time = 0
        self.duration = 0
        self.current_file_path = None # added this to track the file
        self.playback_thread = None
        
        # Matplotlib objects
        self.figure = None
        self.ax = None
        self.canvas = None

        self.setup_ui()

    def setup_ui(self):
        # Top Controls Frame
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=10, pady=10)
        
        # Load Button
        self.btn_load = ctk.CTkButton(controls, text="Load Audio File", 
                                     command=self.load_audio, width=150)
        self.btn_load.pack(side="left", padx=5)
        
        # Play/Stop Buttons
        self.btn_play = ctk.CTkButton(controls, text="Play", state="disabled",
                                     command=self.toggle_play, width=100)
        self.btn_play.pack(side="left", padx=5)
        
        self.lbl_time = ctk.CTkLabel(controls, text="0:00 / 0:00")
        self.lbl_time.pack(side="left", padx=15)
        
        # Color Map Selector
        ctk.CTkLabel(controls, text="Color:").pack(side="right", padx=5)
        self.cmap_var = ctk.StringVar(value="inferno")
        self.combo_cmap = ctk.CTkComboBox(controls, values=["inferno", "magma", "plasma", "viridis"],
                                         variable=self.cmap_var, command=self.redraw_map, width=100)
        self.combo_cmap.pack(side="right", padx=5)

        # The Graph Container
        # We use a standard Frame to hold the matplotlib canvas 
        self.plot_frame = ctk.CTkFrame(self, fg_color="black")
        self.plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # empty graph setup
        self.setup_plot()

    def setup_plot(self):
        # Create the figure with a dark background to match the app
        self.figure = Figure(figsize=(5, 4), dpi=100, facecolor='#1a1a1a')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('black')
        
        # Hide axis initially
        self.ax.axis('off')
        
        # Embed to tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def load_audio(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")]
        )
        
        if file_path:
            self.lbl_time.configure(text="Loading...")
            self.current_file_path = file_path # saving the path for pygame
            self.update() # force UI refresh
            
            # Use the logic class to process the file
            success, name, sr, dur = self.analyzer.load_file(file_path)
            
            if success:
                self.duration = dur
                self.btn_play.configure(state="normal")
                self.lbl_time.configure(text=f"0:00 / {self.format_time(self.duration)}")
                self.draw_spectrogram()
            else:
                self.lbl_time.configure(text="Error loading file")

    def draw_spectrogram(self):
        # Get data from the backend
        S_db, sr = self.analyzer.get_spectrogram_data()
        
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        
        # Draw the spectogram heatmap
        img = librosa.display.specshow(
            S_db, sr=sr, 
            hop_length=HOP_LENGTH,
            x_axis='time', y_axis='hz',
            ax=self.ax, cmap=self.cmap_var.get(),
            rasterized=True
        )
        
        # Styling the graph
        self.ax.set_facecolor('black')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        
        # Set initial view (scroll to start)


        self.ax.set_xlim(0, WINDOW_SIZE)
        
        self.figure.tight_layout()
        self.canvas.draw()

    def redraw_map(self, _):
        if self.analyzer.S_db is not None:
            self.draw_spectrogram()

    def toggle_play(self):
        if not self.is_playing:
            self.player.stop_file() # stop any painter audio
            self.player.stop_array() # stop any raw audio
            
            self.is_playing = True
            self.btn_play.configure(text="Stop", fg_color="red")
            self.btn_load.configure(state="disabled")
            
            self.start_time = time.time()
            
            # Start audio in background thread so UI doesn't freeze
            self.playback_thread = threading.Thread(target=self.run_audio)
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            self.update_view_loop()
            
        else:
            # STOP 
            self.is_playing = False
            self.player.stop_file() # switched to stop_file
            self.btn_play.configure(text="Play", fg_color="#1f6aa5") # restore blue color
            self.btn_load.configure(state="normal")

    def run_audio(self):
        # use pygame to play the file instead (better performance)
        if self.current_file_path:
            self.player.play_file(self.current_file_path)

            # we need a loop to keep the thread alive
            while self.player.is_file_playing() and self.is_playing:
                time.sleep(0.1)

            # cleanup
            self.player.stop_file()

        # when audio finishes naturally
        self.is_playing = False
        # use after to update UI from thread safely
        self.after(0, lambda: self.btn_play.configure(text="Play", fg_color="#1f6aa5"))
        self.after(0, lambda: self.btn_load.configure(state="normal"))

    def update_view_loop(self):
        if self.is_playing and self.ax:
            elapsed = time.time() - self.start_time
            
            if elapsed < self.duration:
                # Scroll the view to the right, Right side is current time, Left side is history
                # This creates a scrolling effect
                self.ax.set_xlim(elapsed - WINDOW_SIZE, elapsed)
                
                # redraw only if needed
                self.canvas.draw_idle()
                
                self.lbl_time.configure(text=f"{self.format_time(elapsed)} / {self.format_time(self.duration)}")
                
                # call this function again in 100ms (slowed down slightly for performance)
                self.after(30, self.update_view_loop)
            else:
                # Reset view when done
                self.ax.set_xlim(0, WINDOW_SIZE)
                self.canvas.draw()

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

# class AnalyzerTab(ctk.CTkFrame):
#     def __init__(self, master, **kwargs):
#         super().__init__(master, **kwargs)
        
#         # simple label for testing
#         self.lbl = ctk.CTkLabel(self, text="Analyzer Tab (In Development)", font=("Arial", 20))
#         self.lbl.pack(pady=40)





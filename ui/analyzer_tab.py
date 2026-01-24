import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import librosa.display
# Added more libraries for the smoother update
import numpy as np
from PIL import Image, ImageTk
import matplotlib.cm as cm
from scipy.interpolate import interp1d

from audio.analyzer import AudioAnalyzer
from audio.player import AudioPlayer
from config import COLOR_BG, WINDOW_SIZE, HOP_LENGTH, HOP_LENGTH_HD, CANVAS_SIZE, EXPORT_DIMENSIONS

class AnalyzerTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.analyzer = AudioAnalyzer()
        self.player = AudioPlayer()

        self.hide_axis_var = ctk.BooleanVar(value=False) # track hide axis
        self.high_res_var = ctk.BooleanVar(value=False) # track high res
        self.log_scale_var = ctk.BooleanVar(value=False) # track log scale

        self.current_hop = HOP_LENGTH # track which resolution we are using

        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.duration = 0
        self.current_file_path = None # added this to track the file
        self.playback_thread = None
        self.playback_position = 0.0
        
        # Canvas rendering state
        self.spectrogram_image = None
        self.tk_image = None
        self.pixels_per_second = 100 # default zoom
        self.cursor_line = None
        
        # Matplotlib objects (kept for export only)
        self.figure = None
        self.ax = None
        # self.canvas = None # We will use tk.Canvas for display

        self.setup_ui()

    def setup_ui(self):
        # Top Controls Frame
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=10, pady=10)
        
        # Load Button
        self.btn_load = ctk.CTkButton(controls, text="Load Audio File", 
                                     command=self.load_audio, width=150)
        self.btn_load.pack(side="left", padx=5)
        
        # Stop Button
        self.btn_stop = ctk.CTkButton(controls, text="Stop", state="disabled",
                                      command=self.stop_audio, width=80, fg_color="#cf3636")
        self.btn_stop.pack(side="left", padx=5)

        # Play/Stop Buttons
        self.btn_play = ctk.CTkButton(controls, text="Play", state="disabled",
                                     command=self.toggle_play, width=100)
        self.btn_play.pack(side="left", padx=5)
        
        self.lbl_time = ctk.CTkLabel(controls, text="0:00 / 0:00")
        self.lbl_time.pack(side="left", padx=15)

        ## Export Image
        self.btn_export = ctk.CTkButton(controls, text="Save Image", state="disabled",
                                       command=self.save_spectrogram_image, width=100,
                                       fg_color="#E59400", text_color="black") 
        self.btn_export.pack(side="left", padx=5)

        # Zoom Slider
        ctk.CTkLabel(controls, text="Zoom:").pack(side="left", padx=(15, 5))
        self.slider_zoom = ctk.CTkSlider(controls, from_=10, to=500, command=self.on_zoom_change)
        self.slider_zoom.set(100)
        self.slider_zoom.pack(side="left", padx=5)
        
        # Color Map Selector
        ctk.CTkLabel(controls, text="Color:").pack(side="right", padx=5)
        self.cmap_var = ctk.StringVar(value="inferno")
        self.combo_cmap = ctk.CTkComboBox(controls, values=["inferno", "magma", "plasma", "viridis"],
                                         variable=self.cmap_var, command=self.redraw_map, width=100)
        self.combo_cmap.pack(side="right", padx=5)

        # Hide Axis from export
        self.chk_axis = ctk.CTkCheckBox(controls, text="Hide Axes", 
                                        variable=self.hide_axis_var, 
                                        command=lambda: self.redraw_map(None),
                                        width=20)
        self.chk_axis.pack(side="right", padx=10)

        # Log Scale Checkbox
        self.chk_log = ctk.CTkCheckBox(controls, text="Log Scale", 
                                        variable=self.log_scale_var, 
                                        command=lambda: self.redraw_map(None),
                                        width=20)
        self.chk_log.pack(side="right", padx=10)


        # High Res Checkbox
        self.chk_hires = ctk.CTkCheckBox(controls, text="High Res", 
                                        variable=self.high_res_var, 
                                        command=self.toggle_resolution,
                                        width=20)
        self.chk_hires.pack(side="right", padx=10)

        # The Graph Container
        # removed the matplotlib canvas for better performance
        self.plot_frame = ctk.CTkFrame(self, fg_color="black")
        self.plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Native Tkinter Canvas for high performance
        self.canvas = tk.Canvas(self.plot_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Bind scroll events
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", self.on_scroll)
        self.canvas.bind("<Button-5>", self.on_scroll)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # Setup Plot for EXPORT ONLY (off-screen)
        self.setup_plot_backend()

    def setup_plot_backend(self):
        # Create figure for later export use
        self.figure = Figure(figsize=(5, 4), dpi=100, facecolor='#1a1a1a')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('black')
        
        # Hide axis initially
        self.ax.axis('off')

    def on_resize(self, event):
        pass
    
    def on_zoom_change(self, value):
        self.pixels_per_second = float(value)
        if self.analyzer.S_db is not None:
             self.generate_spectrogram_image(update_zoom=False)
             
    def on_log_scale_change(self):
        if self.analyzer.S_db is not None:
            self.generate_spectrogram_image()
            
    def redraw_map(self, _):
        if self.analyzer.S_db is not None:
            self.generate_spectrogram_image()

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
                self.btn_stop.configure(state="normal")
                self.btn_export.configure(state="normal") # load export button on success
                self.lbl_time.configure(text=f"0:00 / {self.format_time(self.duration)}")
                
                # zooming
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 100:
                    default_width = self.duration * 100
                    if default_width < canvas_width:
                        new_pps = canvas_width / self.duration
                        new_pps = max(10, min(500, new_pps))
                        self.pixels_per_second = new_pps
                        self.slider_zoom.set(new_pps)
                    else:
                        self.pixels_per_second = 100
                        self.slider_zoom.set(100)
                        
                self.generate_spectrogram_image(update_zoom=False)
            else:
                self.lbl_time.configure(text="Error loading file")


    def generate_spectrogram_image(self, update_zoom=False):
        S_db, sr = self.analyzer.get_spectrogram_data()
        
        if S_db is None:
            return

        # Prepare frequency grid
        data_to_plot = S_db
        if self.log_scale_var.get():
            try:
                n_bins, n_frames = S_db.shape
                freqs_lin = np.linspace(0, sr/2, n_bins)
                freqs_log = np.geomspace(20, sr/2, n_bins)
                f = interp1d(freqs_lin, S_db, axis=0, kind='linear', fill_value="extrapolate")
                data_to_plot = f(freqs_log)
            except Exception as e:
                print(f"Log scale error: {e}")
                data_to_plot = S_db

        # Normalize 0-1
        min_db = -80.0
        max_db = 0.0
        norm_data = (data_to_plot - min_db) / (max_db - min_db)
        norm_data = np.clip(norm_data, 0, 1)
        norm_data = np.flipud(norm_data)
        
        # Colormap
        cmap = cm.get_cmap(self.cmap_var.get()) # Use the selected cmap
        mapped_data = cmap(norm_data)
        img_data = (mapped_data * 255).astype(np.uint8)
        pil_image = Image.fromarray(img_data)
        
        # Dimensions
        canvas_height = self.canvas.winfo_height()
        if canvas_height < 100: canvas_height = 400
        
        target_width = int(self.duration * self.pixels_per_second)
        
        # Resize
        self.spectrogram_image = pil_image.resize((target_width, canvas_height), Image.Resampling.NEAREST)
        self.tk_image = ImageTk.PhotoImage(self.spectrogram_image)
        
        # Draw on Canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw", tags="spectrogram")
        
        # Draw Cursor (Red Line)
        self.cursor_line = self.canvas.create_line(0, 0, 0, canvas_height, fill="red", width=2, tags="cursor")
        
        # Setup scrolling
        self.canvas.configure(scrollregion=(0, 0, target_width, canvas_height))
        self.canvas.xview_moveto(0)
        
    def on_scroll(self, event):
        if not self.tk_image: return
        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.canvas.xview_scroll(1, "units")
        elif event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.canvas.xview_scroll(-1, "units")

    def toggle_play(self):
        # start fresh
        if not self.is_playing:
            self.is_playing = True
            self.is_paused = False
            
            self.btn_play.configure(text="Pause", fg_color="#E59400") # Orange for pause
            self.btn_load.configure(state="disabled")
            self.btn_export.configure(state="disabled")
            
            self.start_time = time.time()
            self.playback_position = 0.0
            
            self.playback_thread = threading.Thread(target=self.run_audio)
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            self.update_view_loop()
            
        # pause/Resume
        else:
            if not self.is_paused:
                # PAUSE
                self.is_paused = True
                self.player.pause_file()
                self.btn_play.configure(text="Resume", fg_color="green")
                self.pause_start_timestamp = time.time()
                
            else:
                # RESUME 
                self.is_paused = False
                self.player.unpause_file()
                self.btn_play.configure(text="Pause", fg_color="#E59400")
                
                # Shift the start time
                pause_duration = time.time() - self.pause_start_timestamp
                self.start_time += pause_duration

    def stop_audio(self):
        self.is_playing = False
        self.is_paused = False
        self.player.stop_file()
        self.btn_play.configure(text="Play", fg_color="#1f6aa5")
        self.btn_load.configure(state="normal")
        self.btn_export.configure(state="normal")
        
        # Reset the cursor position
        self.playback_position = 0.0
        self.canvas.coords(self.cursor_line, 0, 0, 0, self.canvas.winfo_height())
        self.canvas.xview_moveto(0)

    def toggle_resolution(self):
        # Triggered when the High Res box is clicked
        if self.analyzer.audio_data is None:
            return
            
        # recalculate spectrogram
        is_hd = self.high_res_var.get()
        self.current_hop = self.analyzer.recompute_spectrogram(high_res=is_hd)
        
        # redraw with new data
        self.generate_spectrogram_image()

    def save_spectrogram_image(self):
        # render the current view of the canvas to a file at HIGH RES
        S_db, sr = self.analyzer.get_spectrogram_data()
        
        if S_db is None:
            return
            
        # Default filename from loaded audio
        default_name = "spectrogram"
        if self.current_file_path:
            import os
            base = os.path.basename(self.current_file_path)
            name, _ = os.path.splitext(base)
            default_name = f"{name}_{sr}Hz"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")],
            title="Export High-Res Spectrogram"
        )
        
        if file_path:
            try:
                target_height = 2160 
                # Current ratio: 100px/sec at Height=Current
                # New ratio: scaled_pps at Height=2160
                # scale = 2160 / 720 = 3x                  
                current_h = 720 
                scale_factor = target_height / current_h
                
                # Effective Width
                target_width = int((self.duration * self.pixels_per_second) * scale_factor)
                
                print(f"Exporting High Res: {target_width}x{target_height} (Scale: {scale_factor:.1f}x)")
                
                #Log Scale / Normalization
                data_to_plot = S_db
                if self.log_scale_var.get():
                    n_bins, n_frames = S_db.shape
                    freqs_lin = np.linspace(0, sr/2, n_bins)
                    freqs_log = np.geomspace(20, sr/2, n_bins)
                    f = interp1d(freqs_lin, S_db, axis=0, kind='linear', fill_value="extrapolate")
                    data_to_plot = f(freqs_log)
                
                min_db, max_db = -80.0, 0.0
                norm_data = (data_to_plot - min_db) / (max_db - min_db)
                norm_data = np.clip(norm_data, 0, 1)
                norm_data = np.flipud(norm_data)
                
                # add Colormap
                cmap = cm.get_cmap(self.cmap_var.get())
                mapped_data = cmap(norm_data)
                img_data = (mapped_data * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_data)
                
                # resize - LANCZOS for high quality down/up-scaling
                export_img = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                export_img.save(file_path)
                print(f"Saved image to {file_path}")
                
            except Exception as e:
                print(f"Error saving image: {e}")
                import traceback
                traceback.print_exc()

    def run_audio(self):
        if self.current_file_path:
            self.player.play_file(self.current_file_path)
            
            while self.is_playing:
                if self.is_paused:
                    time.sleep(0.1)
                    continue

                if not self.player.is_file_playing():
                    break
                
                time.sleep(0.05)
                
            if not self.is_playing:
               self.player.stop_file() 
            else:
               self.is_playing = False
               self.after(0, lambda: self.stop_audio())
               self.after(0, lambda: self.btn_load.configure(state="normal")) 

    def update_view_loop(self):
        if self.is_playing:
            if not self.is_paused:
                elapsed = time.time() - self.start_time
                self.playback_position = elapsed
                
                if elapsed < self.duration:
                    self.lbl_time.configure(text=f"{self.format_time(elapsed)} / {self.format_time(self.duration)}")
                    cursor_x = elapsed * self.pixels_per_second
                    canvas_h = self.canvas.winfo_height()
                    self.canvas.coords(self.cursor_line, cursor_x, 0, cursor_x, canvas_h)
                    
                    # Auto Scroll Logic
                    visible_w = self.canvas.winfo_width()
                    start_x = self.canvas.canvasx(0)
                    if cursor_x > start_x + (visible_w * 0.8):
                        target_left = cursor_x - (visible_w * 0.5)
                        total_w = self.duration * self.pixels_per_second
                        fraction = target_left / total_w
                        self.canvas.xview_moveto(fraction)
                else:
                     pass
            
            if self.is_playing:
                self.after(30, self.update_view_loop)

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





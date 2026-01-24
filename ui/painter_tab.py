import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import threading
import os

# backend logic
from audio.generator import AudioGenerator
from audio.player import AudioPlayer
from config import COLOR_BG, COLOR_ACCENT, OUTPUT_FILENAME, CANVAS_SIZE, EXPORT_DIMENSIONS

class PainterTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        
        super().__init__(master, **kwargs)

        # logic init
        self.generator = AudioGenerator()
        self.player = AudioPlayer()

        self.last_x = None
        self.last_y = None
        self.canvas_width = CANVAS_SIZE
        self.canvas_height = CANVAS_SIZE
        self.generated_file_path = None


        # This is what gets sent to the audio generator
        self.image = Image.new("L", (self.canvas_width, self.canvas_height), "black")
        self.draw = ImageDraw.Draw(self.image)

        self.setup_ui()

    def setup_ui(self):
        # eft for Canvas, Right for the Controls
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Drawing Canvas
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        lbl_canvas = ctk.CTkLabel(left_frame, text="Draw Spectrogram", font=("Arial", 16, "bold"))
        lbl_canvas.pack(pady=(10, 5))

        # We use standard tk.Canvas to draw on
        self.draw_canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height, 
                                bg=COLOR_BG, cursor="crosshair", highlightthickness=0)
        self.draw_canvas.pack(pady=10)

        # Bind mouse events
        self.draw_canvas.bind("<Button-1>", self.start_paint)
        self.draw_canvas.bind("<B1-Motion>", self.paint)
        self.draw_canvas.bind("<ButtonRelease-1>", self.stop_paint)

        # Canvas Tools
        # RIGHT SIDE: Controls
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        #MOVED TOOLS TO RIGHT FRAME
        tools_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        tools_frame.pack(pady=10, fill="x", padx=10)

        self.btn_clear = ctk.CTkButton(tools_frame, text="Clear Canvas", fg_color="#cf3636", 
                                       command=self.clear_canvas)
        self.btn_clear.pack(pady=5, fill="x")

        self.btn_load = ctk.CTkButton(tools_frame, text="Load Image", fg_color="#E59400", 
                                      text_color="black", command=self.load_image)
        self.btn_load.pack(pady=5, fill="x")

        ctk.CTkLabel(tools_frame, text="Brush Size:").pack(pady=(10,0))
        self.slider_brush = ctk.CTkSlider(tools_frame, from_=1, to=30, number_of_steps=29)
        self.slider_brush.set(10)
        self.slider_brush.pack(pady=5)

        #----------------------------

        ctk.CTkLabel(right_frame, text="Settings", font=("Arial", 16, "bold")).pack(pady=10)

        # Duration Slider
        self.lbl_duration = ctk.CTkLabel(right_frame, text="Duration: 3s")
        self.lbl_duration.pack(pady=5)
        self.slider_duration = ctk.CTkSlider(right_frame, from_=1, to=10, number_of_steps=9, 
                                             command=self.on_duration_slider)
        self.slider_duration.set(3.0)
        self.slider_duration.pack(pady=5, padx=20)
        
        # Duration Entry
        self.entry_duration = ctk.CTkEntry(right_frame, width=60, placeholder_text="s")
        self.entry_duration.insert(0, "3")
        self.entry_duration.bind("<Return>", self.on_duration_entry)
        self.entry_duration.pack(pady=2)
        
        ctk.CTkLabel(right_frame, text="Sample Rate (Hz):").pack(pady=(10,2))
        self.entry_samplerate = ctk.CTkEntry(right_frame, width=80)
        self.entry_samplerate.insert(0, "48000")
        self.entry_samplerate.pack(pady=2)

        # Quality Slider
        self.lbl_quality = ctk.CTkLabel(right_frame, text="Quality: 16 iters")
        self.lbl_quality.pack(pady=5)
        self.slider_quality = ctk.CTkSlider(right_frame, from_=1, to=64, number_of_steps=63, 
                                            command=self.on_quality_slider)
        self.slider_quality.set(16)
        self.slider_quality.pack(pady=5, padx=20)
        
        # Pitch Shift Slider
        self.lbl_pitch = ctk.CTkLabel(right_frame, text="Pitch: 0 semitones")
        self.lbl_pitch.pack(pady=5)
        self.slider_pitch = ctk.CTkSlider(right_frame, from_=-12, to=12, number_of_steps=48,
                                          command=self.on_pitch_slider)
        self.slider_pitch.set(0)
        self.slider_pitch.pack(pady=5, padx=20)
        
        # Generate Button
        self.btn_convert = ctk.CTkButton(right_frame, text="GENERATE AUDIO", height=50, 
                                         fg_color=COLOR_ACCENT, text_color="black",
                                         font=("Arial", 14, "bold"),
                                         command=self.start_generation)
        self.btn_convert.pack(pady=30, padx=20, fill="x")

        # Playback Controls
        self.btn_play = ctk.CTkButton(right_frame, text="Play", state="disabled", 
                                      fg_color="green", command=self.play_audio)
        self.btn_play.pack(pady=5, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(right_frame, text="Ready to draw.")
        self.status_label.pack(side="bottom", pady=20)

    # logic for drawing
    def start_paint(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def paint(self, event):
        brush_size = int(self.slider_brush.get())
        x, y = event.x, event.y
        
        if self.last_x:
            # Draw on visible screen
            self.draw_canvas.create_line(self.last_x, self.last_y, x, y, 
                                         width=brush_size * 2, fill=COLOR_ACCENT,
                                         capstyle=tk.ROUND, smooth=True)
            
            # Draw on internal PIL image scaled
            # If scale_factor is 0.5 (shown half size), we must multiply coords by 2 (divide by 0.5)
            # to draw on the big image.
            
            sf = getattr(self, 'scale_factor', 1.0)
            
            real_lx = self.last_x / sf
            real_ly = self.last_y / sf
            real_x = x / sf
            real_y = y / sf
            real_width = (brush_size * 2) / sf
            
            self.draw.line([real_lx, real_ly, real_x, real_y], 
                           fill=255, width=int(real_width), joint="curve")

        self.last_x = x
        self.last_y = y

    def stop_paint(self, event):
        self.last_x = None
        self.last_y = None


    def load_image(self):
            file_path = filedialog.askopenfilename(
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
            )

            if file_path:
                # open the image and convert to grayscale
                # KEEP FULL RESOLUTION loaded_img
                self.image = Image.open(file_path).convert('L')
                self.draw = ImageDraw.Draw(self.image)
                
                # Display Image (Scaled to fit UI)
                display_img = self.image.copy()
                self.scale_factor = 1.0
                
                max_limit = 1000
                if display_img.width > max_limit or display_img.height > max_limit:
                    display_img.thumbnail((max_limit, max_limit), Image.Resampling.LANCZOS)
                    # Calculate scale factor (Display / Original)
                    self.scale_factor = display_img.width / float(self.image.width)

                w, h = display_img.size

                # match canvas to Display size
                self.canvas_width = w
                self.canvas_height = h
                
                EXPORT_DIMENSIONS['w'] = self.image.width
                EXPORT_DIMENSIONS['h'] = self.image.height
                # ----------------------------########

                # resize the visible tkinter canvas so it fits the display image
                self.draw_canvas.configure(width=w, height=h)
                
                # display on screen
                self.tk_image_ref = ImageTk.PhotoImage(display_img)
                self.draw_canvas.create_image(0, 0, image=self.tk_image_ref, anchor="nw")
                self.status_label.configure(text=f"Loaded: {self.image.width}x{self.image.height} (Shown: {w}x{h})")
                
                import re
                sr_match = re.search(r'_(\d+)Hz', file_path)
                if sr_match:
                    sr_value = sr_match.group(1)
                    self.entry_samplerate.delete(0, "end")
                    self.entry_samplerate.insert(0, sr_value)
                
                dur_match = re.search(r'_([\d.]+)s', file_path)
                if dur_match:
                    dur_value = dur_match.group(1)
                    self.entry_duration.delete(0, "end")
                    self.entry_duration.insert(0, dur_value)
                    dur_float = float(dur_value)
                    if 1 <= dur_float <= 10:
                        self.slider_duration.set(dur_float)
                    self.lbl_duration.configure(text=f"Duration: {dur_value}s")

    def clear_canvas(self):
        self.draw_canvas.delete("all")

        # reset to default size
        self.canvas_width = CANVAS_SIZE
        self.canvas_height = CANVAS_SIZE
        
        # reset shared mem
        EXPORT_DIMENSIONS['w'] = CANVAS_SIZE
        EXPORT_DIMENSIONS['h'] = CANVAS_SIZE
        # ---------------------------

        # Reset the PIL image to black
        self.draw_canvas.configure(width=self.canvas_width, height=self.canvas_height)
        self.image = Image.new("L", (self.canvas_width, self.canvas_height), "black")
        self.draw = ImageDraw.Draw(self.image)
        self.tk_image_ref = None
        self.btn_play.configure(state="disabled")
        self.status_label.configure(text="Canvas cleared")

    def on_duration_slider(self, value):
        d = int(self.slider_duration.get())
        self.lbl_duration.configure(text=f"Duration: {d}s")
        self.entry_duration.delete(0, "end")
        self.entry_duration.insert(0, str(d))
    
    def on_quality_slider(self, value):
        q = int(self.slider_quality.get())
        self.lbl_quality.configure(text=f"Quality: {q} iters")
    
    def on_pitch_slider(self, value):
        p = self.slider_pitch.get()
        self.lbl_pitch.configure(text=f"Pitch: {p:.1f} semitones")
    
    def on_duration_entry(self, event):
        try:
            value = float(self.entry_duration.get())
            if value > 0:
                # Only update slider if value is within range
                if 1 <= value <= 10:
                    self.slider_duration.set(value)
                # Always update the label
                self.lbl_duration.configure(text=f"Duration: {value}s")
        except ValueError:
            pass

    # logic for the sound
    def start_generation(self):
        # Stop any playback
        self.player.stop_file()

        # Ask where to save
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            initialfile="generated_audio.wav",
            filetypes=[("WAV Audio", "*.wav")],
            title="Save Generated Audio"
        )
        
        if not file_path:
            return

        # thread running to avoid freezing
        self.btn_convert.configure(state="disabled", text="Computing...")
        self.status_label.configure(text="Generating audio...")
        
        # Read duration from entry field (allows values beyond slider range)
        try:
            duration = float(self.entry_duration.get())
        except ValueError:
            duration = int(self.slider_duration.get())
        
        try:
            sample_rate = int(self.entry_samplerate.get())
        except ValueError:
            sample_rate = 48000
        
        iterations = int(self.slider_quality.get())
        pitch_shift = self.slider_pitch.get()
        
        thread = threading.Thread(target=self.run_generation, args=(duration, iterations, file_path, pitch_shift, sample_rate))
        thread.start()

    def run_generation(self, duration, iterations, output_path, pitch_shift, sample_rate):
        # Call the backend generator
        # We pass self.image, which is the Pillow object we drew on
        filename, _ = self.generator.generate_from_image(self.image, duration, iterations, output_path, pitch_shift, sample_rate)
        
        self.after(0, self.finish_generation, filename)

    def finish_generation(self, filename):
        self.btn_convert.configure(state="normal", text="GENERATE AUDIO")
        
        if filename:
            self.generated_file_path = filename
            self.status_label.configure(text=f"Saved to: {os.path.basename(filename)}")
            self.btn_play.configure(state="normal")
        else:
            self.status_label.configure(text="Error generating audio.")

    def play_audio(self):
        if self.generated_file_path and os.path.exists(self.generated_file_path):
            self.player.play_file(self.generated_file_path)


            
# class PainterTab(ctk.CTkFrame):
#     def __init__(self, master, **kwargs):
#         super().__init__(master, **kwargs)
        
#         # simple label for testing
#         self.lbl = ctk.CTkLabel(self, text="Painter Tab (In development)", font=("Arial", 20))
#         self.lbl.pack(pady=40)
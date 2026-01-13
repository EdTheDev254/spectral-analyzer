import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import threading
import os

# backend logic
from audio.generator import AudioGenerator
from audio.player import AudioPlayer
from config import COLOR_BG, COLOR_ACCENT, OUTPUT_FILENAME

class PainterTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        
        super().__init__(master, **kwargs)

        # logic init
        self.generator = AudioGenerator()
        self.player = AudioPlayer()

        self.last_x = None
        self.last_y = None
        self.canvas_width = 600
        self.canvas_height = 400


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
        tools_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        tools_frame.pack(pady=10, fill="x", padx=20)

        self.btn_clear = ctk.CTkButton(tools_frame, text="Clear Canvas", fg_color="#cf3636", 
                                       command=self.clear_canvas)
        self.btn_clear.pack(side="left", padx=10, expand=True)

        ctk.CTkLabel(tools_frame, text="Brush Size:").pack(side="left", padx=5)
        self.slider_brush = ctk.CTkSlider(tools_frame, from_=1, to=30, number_of_steps=29)
        self.slider_brush.set(10)
        self.slider_brush.pack(side="left", padx=5)

        # The Controls
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(right_frame, text="Settings", font=("Arial", 16, "bold")).pack(pady=10)

        # Duration Slider
        self.lbl_duration = ctk.CTkLabel(right_frame, text="Duration: 3s")
        self.lbl_duration.pack(pady=5)
        self.slider_duration = ctk.CTkSlider(right_frame, from_=1, to=10, number_of_steps=9, 
                                             command=self.update_labels)
        self.slider_duration.set(3.0)
        self.slider_duration.pack(pady=5, padx=20)

        # Quality Slider
        self.lbl_quality = ctk.CTkLabel(right_frame, text="Quality: 16 iters")
        self.lbl_quality.pack(pady=5)
        self.slider_quality = ctk.CTkSlider(right_frame, from_=1, to=64, number_of_steps=63, 
                                            command=self.update_labels)
        self.slider_quality.set(16)
        self.slider_quality.pack(pady=5, padx=20)

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
            
            # Draw on invisible PIL image (White)
            self.draw.line([self.last_x, self.last_y, x, y], 
                           fill=255, width=brush_size * 2, joint="curve")

        self.last_x = x
        self.last_y = y

    def stop_paint(self, event):
        self.last_x = None
        self.last_y = None

    def clear_canvas(self):
        self.draw_canvas.delete("all")
        # Reset the PIL image to black
        self.image = Image.new("L", (self.canvas_width, self.canvas_height), "black")
        self.draw = ImageDraw.Draw(self.image)
        self.btn_play.configure(state="disabled")

    def update_labels(self, value):
        d = int(self.slider_duration.get())
        q = int(self.slider_quality.get())
        self.lbl_duration.configure(text=f"Duration: {d}s")
        self.lbl_quality.configure(text=f"Quality: {q} iters")

    # logic for the sound
    def start_generation(self):
        # force the player to release the file lock before we overwrite it // fix the error after stpoing for new drawing
        self.player.stop_file()

        # thread running to avoid freezing
        self.btn_convert.configure(state="disabled", text="Computing...")
        self.status_label.configure(text="Generating audio...")
        
        duration = int(self.slider_duration.get())
        iterations = int(self.slider_quality.get())
        
        thread = threading.Thread(target=self.run_generation, args=(duration, iterations))
        thread.start()

    def run_generation(self, duration, iterations):
        # Call the backend generator
        # We pass self.image, which is the Pillow object we drew on
        filename, _ = self.generator.generate_from_image(self.image, duration, iterations)
        
        self.after(0, self.finish_generation, filename)

    def finish_generation(self, filename):
        self.btn_convert.configure(state="normal", text="GENERATE AUDIO")
        
        if filename:
            self.status_label.configure(text="Generation Complete!")
            self.btn_play.configure(state="normal")
        else:
            self.status_label.configure(text="Error generating audio.")

    def play_audio(self):
        if os.path.exists(OUTPUT_FILENAME):
            self.player.play_file(OUTPUT_FILENAME)


            
# class PainterTab(ctk.CTkFrame):
#     def __init__(self, master, **kwargs):
#         super().__init__(master, **kwargs)
        
#         # simple label for testing
#         self.lbl = ctk.CTkLabel(self, text="Painter Tab (In development)", font=("Arial", 20))
#         self.lbl.pack(pady=40)



import customtkinter as ctk

class PainterTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # simple label for testing
        self.lbl = ctk.CTkLabel(self, text="Painter Tab (In development)", font=("Arial", 20))
        self.lbl.pack(pady=40)
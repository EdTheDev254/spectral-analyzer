import customtkinter as ctk

class AnalyzerTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # simple label for testing
        self.lbl = ctk.CTkLabel(self, text="Analyzer Tab (In Development)", font=("Arial", 20))
        self.lbl.pack(pady=40)
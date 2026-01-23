import customtkinter as ctk
from ui.painter_tab import PainterTab
from ui.analyzer_tab import AnalyzerTab
from config import COLOR_BG

# set the theme globally
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SpectralStudio(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spectral Audio Studio")
        self.geometry("1400x900")
        
        # grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()

    def setup_ui(self):
        # create the tab container
        self.tabview = ctk.CTkTabview(self, width=1380, height=880)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.tab_paint_ref = self.tabview.add("Spectral Painter")
        self.tab_analyze_ref = self.tabview.add("Spectral Analyzer")
        # self.tab_scroll_ref = self.tabview.add("Scrollable View")
        
        # initialize the painter tab script
        self.painter = PainterTab(master=self.tab_paint_ref)
        self.painter.pack(fill="both", expand=True)
        
        # initialize the analyzer tab script
        self.analyzer = AnalyzerTab(master=self.tab_analyze_ref)
        self.analyzer.pack(fill="both", expand=True)

    def on_closing(self):
        # clean up threads or audio streams if needed later
        self.destroy()
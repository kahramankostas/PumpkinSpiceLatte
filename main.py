import customtkinter as ctk
import webbrowser
import threading
from logic import search_in_srts, get_video_url

# Configuration
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Subtitle Scene Finder")
        self.geometry("800x600")

        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Results area expands

        # 1. Search Area
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.entry = ctk.CTkEntry(self.search_frame, placeholder_text="Kelimeyi buraya yazın...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.entry.bind("<Return>", lambda event: self.start_search())

        self.search_button = ctk.CTkButton(self.search_frame, text="Ara", command=self.start_search)
        self.search_button.pack(side="right", padx=(0, 10), pady=10)

        # 2. Results Area
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Sonuçlar")
        self.results_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def start_search(self):
        query = self.entry.get()
        if not query:
            return
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        # Show loading...
        loading_label = ctk.CTkLabel(self.results_frame, text="Aranıyor...")
        loading_label.pack(pady=10)
        
        # Run search in a separate thread to not freeze GUI
        threading.Thread(target=self.perform_search, args=(query,), daemon=True).start()

    def perform_search(self, query):
        # limit=None to get all results
        results = search_in_srts(query, limit=None)
        
        # Update GUI on main thread
        self.after(0, self.display_results, results)

    def display_results(self, results):
        # Clear "Aranıyor..."
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            no_res = ctk.CTkLabel(self.results_frame, text="Sonuç bulunamadı.")
            no_res.pack(pady=10)
            return
        
        # Show count
        count_label = ctk.CTkLabel(self.results_frame, text=f"{len(results)} sonuç bulundu.")
        count_label.pack(pady=(0, 10))

        for idx, item in enumerate(results):
            self.create_result_item(item, idx)

    def create_result_item(self, item, idx):
        # item: {'filename': ..., 'timestamp': ..., 'text': ..., 'seconds': ...}
        
        card = ctk.CTkFrame(self.results_frame)
        card.pack(fill="x", padx=10, pady=5)
        
        # Title & Time
        title_text = f"{item['filename']} - [{item['timestamp']}]"
        lbl_title = ctk.CTkLabel(card, text=title_text, font=("Arial", 12, "bold"), anchor="w")
        lbl_title.pack(fill="x", padx=10, pady=(10, 0))
        
        # Context Text
        lbl_text = ctk.CTkLabel(card, text=item['text'], justify="left", wraplength=700, anchor="w", text_color="gray75")
        lbl_text.pack(fill="x", padx=10, pady=(5, 10))
        
        # Button
        btn_action = ctk.CTkButton(card, text="İzle (Tarayıcıda Aç)", 
                                   command=lambda f=item['filename'], s=item['seconds']: self.open_video(f, s))
        btn_action.pack(anchor="e", padx=10, pady=(0, 10))

    def open_video(self, filename, seconds):
        url = get_video_url(filename, seconds)
        if url:
             webbrowser.open(url)
        else:
             print(f"URL not found for {filename}")
             # Optionally show an error dialog
             top = ctk.CTkToplevel(self)
             top.title("Hata")
             ctk.CTkLabel(top, text="Video URL'si excel dosyasında bulunamadı.").pack(padx=20, pady=20)
             
             # Also debug hint on console
             print("Debug info: Check if filenames in folder match titles in Excel.")

if __name__ == "__main__":
    app = App()
    app.mainloop()

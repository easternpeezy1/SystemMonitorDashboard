import tkinter as tk
from PIL import Image, ImageTk
import threading
import time

def show_splash():
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.geometry("400x300")
    
    # Center window
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 300) // 2
    splash.geometry(f"400x300+{x}+{y}")
    
    # Add text
    label = tk.Label(splash, text="System Monitor Dashboard", 
                     font=("Arial", 20, "bold"), bg="#667eea", fg="white")
    label.pack(expand=True)
    
    loading = tk.Label(splash, text="Loading...", 
                      font=("Arial", 12), bg="#667eea", fg="white")
    loading.pack()
    
    # Auto close after 2 seconds
    splash.after(2000, splash.destroy)
    splash.mainloop()

# Run in your app.py before app.run()
threading.Thread(target=show_splash, daemon=True).start()
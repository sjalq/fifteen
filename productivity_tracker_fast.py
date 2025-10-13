import tkinter as tk
import json
import os
from datetime import datetime
import threading
import time
import sys

class ProductivityApp:
    def __init__(self):
        self.running = True
        self.data_file = "productivity_log.json"
        self.data = self.load_existing_data()
        self.timer_enabled = self.data.get("settings", {}).get("timer_enabled", True)
        
        # Create root window but keep it hidden
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Pre-create the popup window but keep it hidden
        self.create_popup()
        self.window.withdraw()
        
        # Lazy load tray icon in background
        threading.Thread(target=self._setup_tray_delayed, daemon=True).start()
        
        # Single timer thread for everything
        threading.Thread(target=self.timer_loop, daemon=True).start()
        
        # Run tkinter main loop
        self.root.mainloop()
    
    def _setup_tray_delayed(self):
        """Load heavy imports and setup tray after startup"""
        time.sleep(0.1)  # Let tkinter initialize first
        
        # Lazy import heavy modules
        global pystray, Image, ImageDraw, MenuItem
        from PIL import Image, ImageDraw
        import pystray
        from pystray import MenuItem
        
        # Create simple icon
        icon_image = Image.new("RGBA", (64, 64), color=(0, 120, 215))
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle([(16, 16), (48, 48)], fill=(255, 255, 255))
        
        # Create menu
        menu = pystray.Menu(
            MenuItem('Show Popup', lambda: self.root.after(0, self.toggle_popup), default=True),
            pystray.Menu.SEPARATOR,
            MenuItem(lambda text: f"Timer: {'ON' if self.timer_enabled else 'OFF'}", 
                    lambda: self.root.after(0, self.toggle_timer)),
            pystray.Menu.SEPARATOR,
            MenuItem('Quit', lambda: self.root.after(0, self.quit_application))
        )
        
        # Create and run icon
        self.icon = pystray.Icon("ProductivityTracker", icon_image, "Productivity Tracker", menu)
        self.icon.run()
    
    def load_existing_data(self):
        """Load existing data from JSON file"""
        default_data = {"priorities": [], "actions": [], "settings": {"timer_enabled": True}}
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Ensure structure
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]
                    return data
            except:
                pass
        return default_data
    
    def save_data(self):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def create_popup(self):
        """Create the popup window once and reuse it"""
        self.window = tk.Toplevel(self.root)
        self.window.title("Productivity Check")
        self.window.protocol("WM_DELETE_WINDOW", self.hide_popup)
        
        # Set window size
        win_width = self.window.winfo_screenwidth() // 4
        win_height = self.window.winfo_screenheight() // 2
        x = (self.window.winfo_screenwidth() // 2) - (win_width // 2)
        y = (self.window.winfo_screenheight() // 2) - (win_height // 2)
        self.window.geometry(f'{win_width}x{win_height}+{x}+{y}')
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        for i in [2, 4, 6]:
            self.window.grid_rowconfigure(i, weight=1)
        
        # Time label
        self.time_label = tk.Label(self.window, text="", font=("Segoe UI", 14))
        self.time_label.grid(row=0, column=0, pady=10)
        
        # Top 3 priorities
        tk.Label(self.window, text="Your top 3 current priorities:", font=("Segoe UI", 12, "bold")).grid(row=1, column=0, sticky="w", padx=10)
        self.top3_entry = tk.Text(self.window, height=4, font=("Segoe UI", 11))
        self.top3_entry.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # Past 15 minutes
        tk.Label(self.window, text="What did you get done in the past 15 minutes?", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w", padx=10)
        self.past_entry = tk.Text(self.window, height=4, font=("Segoe UI", 11))
        self.past_entry.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        
        # Next 15 minutes
        tk.Label(self.window, text="What's your aim for the next 15 minutes?", font=("Segoe UI", 12, "bold")).grid(row=5, column=0, sticky="w", padx=10)
        self.next_entry = tk.Text(self.window, height=4, font=("Segoe UI", 11))
        self.next_entry.grid(row=6, column=0, sticky="nsew", padx=10, pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=7, column=0, pady=10)
        
        tk.Button(button_frame, text="Submit", command=self.submit, bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        self.close_button = tk.Button(button_frame, text="Close", command=self.confirm_close, bg="#FF5252", fg="white", font=("Segoe UI", 11, "bold"), padx=10, pady=5)
        self.close_button.pack(side=tk.LEFT, padx=5)
    
    def toggle_popup(self):
        """Show or hide popup"""
        if self.window.state() == 'withdrawn':
            self.show_popup()
        else:
            self.hide_popup()
    
    def show_popup(self):
        """Show the popup window"""
        # Update time
        self.time_label.config(text=f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Load latest top3
        if self.data["priorities"]:
            self.top3_entry.delete("1.0", tk.END)
            self.top3_entry.insert("1.0", self.data["priorities"][-1]["text"])
        
        # Show window
        self.window.deiconify()
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.attributes('-topmost', False)
        self.top3_entry.focus_set()
    
    def hide_popup(self):
        """Hide the popup window"""
        self.window.withdraw()
    
    def submit(self):
        """Save entries and hide window"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get text
        past_text = self.past_entry.get("1.0", tk.END).strip()
        next_text = self.next_entry.get("1.0", tk.END).strip()
        top3_text = self.top3_entry.get("1.0", tk.END).strip()
        
        # Save action
        self.data["actions"].append({
            "time": timestamp,
            "past_15": past_text,
            "next_15": next_text
        })
        
        # Save priority if changed
        if not self.data["priorities"] or top3_text != self.data["priorities"][-1]["text"]:
            self.data["priorities"].append({
                "time": timestamp,
                "text": top3_text
            })
        
        self.save_data()
        
        # Clear fields
        self.past_entry.delete("1.0", tk.END)
        self.next_entry.delete("1.0", tk.END)
        
        # Hide window
        self.hide_popup()
    
    def toggle_timer(self):
        """Toggle timer on/off"""
        self.timer_enabled = not self.timer_enabled
        self.data["settings"]["timer_enabled"] = self.timer_enabled
        self.save_data()
        
        # Update menu if icon exists
        if hasattr(self, 'icon'):
            self.icon.update_menu()
    
    def timer_loop(self):
        """Single timer loop for 15-minute popups"""
        while self.running:
            if self.timer_enabled:
                now = datetime.now()
                # Calculate seconds until next 15-minute mark
                minutes_past = now.minute % 15
                if minutes_past == 0 and now.second < 2:
                    # Show popup
                    self.root.after(0, self.show_popup)
                    time.sleep(60)  # Wait a minute to avoid duplicate
                else:
                    # Sleep until next check
                    time.sleep(10)
            else:
                time.sleep(30)  # Check less frequently when disabled
    
    def confirm_close(self):
        """Two-step close button"""
        if self.close_button["text"] == "Close":
            self.close_button.config(text="Sure?")
        else:
            self.quit_application()
    
    def quit_application(self):
        """Clean shutdown"""
        self.running = False
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.quit()
        sys.exit(0)

if __name__ == "__main__":
    app = ProductivityApp()
import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import datetime
import threading
import time
import queue
import sys
from PIL import Image, ImageDraw, ImageTk

class ProductivityApp:
    def __init__(self):
        self.window = None
        self.running = True
        self.data_file = "productivity_log.json"
        self.entries = self.load_existing_data()
        self.popup_queue = queue.Queue()
        
        # Create initial window
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Start the timer in a separate thread
        self.timer_thread = threading.Thread(target=self.schedule_popup)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        # Show popup immediately upon launch
        self.root.after(100, self.create_popup)
        
        # Check queue periodically for popup requests
        self.root.after(1000, self.check_popup_queue)
        
        # Add a keyboard shortcut for testing (Alt+P)
        self.root.bind_all("<Alt-p>", lambda e: self.direct_show_popup())
        
        # Set protocol for root window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        # Start the main loop
        self.root.mainloop()
        
    def direct_show_popup(self):
        """Directly show the popup without going through the queue"""
        print("direct_show_popup called")  # Debug print
        
        # If window doesn't exist or was destroyed, create a new one
        if self.window is None or not self.window.winfo_exists():
            print("Window doesn't exist, creating new one")
            self.create_popup()
            return
            
        # If window exists but is hidden, show it
        try:
            print("Window exists, bringing to front")
            # Make sure window isn't iconified (minimized)
            if self.window.state() == 'iconic':
                self.window.deiconify()
                
            # Make sure window is visible
            self.window.attributes('-alpha', 1.0)  # Make sure it's visible
            self.window.attributes('-topmost', True)  # Bring to top
            self.window.lift()  # Lift above other windows
            self.window.focus_force()  # Force focus
            
            # Update window to ensure changes take effect
            self.window.update_idletasks()
            self.window.update()
            
            # Flash the window to get attention
            for i in range(2):
                self.window.attributes('-alpha', 0.5)
                self.window.update_idletasks()
                time.sleep(0.1)
                self.window.attributes('-alpha', 1.0)
                self.window.update_idletasks()
                time.sleep(0.1)
        except Exception as e:
            print(f"Error showing window: {e}")
            # If there was an error, create a new popup
            self.create_popup()
    
    def show_popup(self):
        """Schedule popup to be shown from main thread"""
        print("show_popup called")  # Debug print
        self.popup_queue.put(True)
    
    def on_quit(self):
        """Clean up resources and exit"""
        # End the application
        self.running = False
        self.root.quit()
        self.root.destroy()

    def load_existing_data(self):
        """Load existing data from JSON file if it exists"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self):
        """Save current entries to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.entries, f, indent=4)

    def check_popup_queue(self):
        """Check if any popups are requested"""
        try:
            if not self.popup_queue.empty():
                self.popup_queue.get(False)
                self.create_popup()
        except queue.Empty:
            pass
        finally:
            if self.running:
                self.root.after(1000, self.check_popup_queue)
            
    def create_popup(self):
        """Create and display a productivity check popup"""
        print("create_popup called")  # Debug print
        # If a window already exists, just bring it to front instead of creating a new one
        if self.window is not None and self.window.winfo_exists():
            print("Window exists in create_popup, bringing to front")  # Debug print
            self.window.deiconify()  # Restore if minimized
            self.window.lift()  # Bring to front
            self.window.focus_force()  # Focus the window
            return

        # Record the timestamp when the popup is initiated
        self.current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
        self.window = tk.Toplevel(self.root)
        self.window.title("Productivity Check")
        self.window.geometry("400x300")
        
        # Make window resizable
        self.window.resizable(True, True)
        
        # Make window always on top
        self.window.attributes('-topmost', True)
        
        # Hide from taskbar
        self.window.withdraw()  # First withdraw to not flash on taskbar
        self.window.attributes('-toolwindow', True)  # Set as tool window (hides from taskbar on Windows)
        self.window.deiconify()  # Now show it again
        
        # Handle window close event to hide instead of close
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Center the window on screen
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        # Configure the main frame to expand
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(2, weight=1)  # Past entry row
        self.window.grid_rowconfigure(4, weight=1)  # Next entry row

        # Current time label
        current_time = datetime.now().strftime("%H:%M")
        time_label = tk.Label(self.window, text=f"Time: {current_time}", font=("Arial", 12))
        time_label.grid(row=0, column=0, pady=10)

        # Past 15 minutes question
        past_label = tk.Label(self.window, text="What did you get done in the past 15 minutes?")
        past_label.grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.past_entry = tk.Text(self.window, height=4, width=40)
        self.past_entry.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # Next 15 minutes question
        next_label = tk.Label(self.window, text="What's your aim for the next 15 minutes?")
        next_label.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.next_entry = tk.Text(self.window, height=4, width=40)
        self.next_entry.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)

        # Button frame for Submit and Quit buttons
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=5, column=0, pady=10)
        
        # Submit button
        self.submit_button = tk.Button(button_frame, text="Submit", command=self.submit)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Quit button
        quit_button = tk.Button(button_frame, text="Quit", command=self.on_quit)
        quit_button.pack(side=tk.LEFT, padx=5)

        # Set tab order
        self.past_entry.focus_set()
        
        # Override tab behavior
        self.past_entry.bind("<Tab>", self.focus_next_widget)
        self.next_entry.bind("<Tab>", self.focus_next_widget)
        self.submit_button.bind("<Tab>", self.focus_next_widget)
        quit_button.bind("<Tab>", self.focus_next_widget)

        # Keep window running
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def focus_next_widget(self, event):
        """Move focus to next widget when Tab is pressed"""
        event.widget.tk_focusNext().focus()
        return "break"  # Prevents the default Tab behavior
        
    def submit(self):
        """Handle form submission"""
        # Use the timestamp from when the popup was initiated
        past_text = self.past_entry.get("1.0", tk.END).strip()
        next_text = self.next_entry.get("1.0", tk.END).strip()

        # Store the entry
        self.entries[self.current_timestamp] = {
            "past_15": past_text,
            "next_15": next_text
        }
        
        self.save_data()
        
        if self.window.winfo_exists():
            self.window.destroy()
            self.window = None

    def on_closing(self):
        """Handle window closing event"""
        # Save current data
        self.submit()
        # Hide the window instead of destroying it
        self.hide_window()
        
    def hide_window(self):
        """Hide the window instead of closing it"""
        print("Hiding window instead of closing")  # Debug print
        if self.window is not None and self.window.winfo_exists():
            self.window.withdraw()

    def schedule_popup(self):
        """Schedule popups every 15 minutes"""
        while self.running:
            now = datetime.now()
            # Calculate minutes until next 15-minute mark
            minutes = now.minute % 15
            seconds_to_wait = 0 if minutes == 0 else (15 - minutes) * 60 - now.second
            
            # Wait until next 15-minute mark
            if seconds_to_wait > 0:
                time.sleep(seconds_to_wait)
            
            if self.running:
                # Queue a popup request instead of creating one directly
                self.popup_queue.put(True)
                
                # Sleep for a short time to avoid creating multiple popups
                time.sleep(60)  # Wait a minute before checking again

if __name__ == "__main__":
    app = ProductivityApp() 
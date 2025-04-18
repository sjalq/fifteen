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
        self.data = self.load_existing_data()
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
        
        # Add a keyboard shortcut for quitting (Alt+Q)
        self.root.bind_all("<Alt-q>", lambda e: self.on_quit())
        
        # Set protocol for root window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        # Start the main loop
        self.root.mainloop()
        
    def direct_show_popup(self):
        """Directly show the popup without going through the queue"""
        print("direct_show_popup called")  # Debug print
        
        # Always create a new popup with fresh timestamp
        if self.window is not None and self.window.winfo_exists():
            # If window is minimized or visible, destroy it to create a new one
            print("Destroying existing window to create a new one")
            self.window.destroy()
            self.window = None
            
        # Create a new popup
        self.create_popup()
        
    def update_time_label(self):
        """Update the time label with current time including seconds"""
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=f"Time: {current_time}")
            
            # No continuous updates - only update when focus is gained
            
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
        # Default structure with empty lists for priorities and actions
        default_data = {
            "priorities": [],
            "actions": []
        }
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    
                    # Check if we need to migrate from old format to new format
                    if not isinstance(data, dict) or "priorities" not in data or "actions" not in data:
                        # Create a backup of the original data file
                        backup_file = f"{self.data_file}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        try:
                            import shutil
                            shutil.copy2(self.data_file, backup_file)
                            print(f"Created backup of original data file: {backup_file}")
                        except Exception as e:
                            print(f"Warning: Failed to create backup: {e}")
                            
                        # This is the old format, migrate it
                        return self.migrate_old_data(data)
                    
                    return data
            except Exception as e:
                print(f"Error loading data: {e}")
                return default_data
        return default_data
    
    def migrate_old_data(self, old_data):
        """Migrate data from old format to new format"""
        new_data = {
            "priorities": [],
            "actions": []
        }
        
        # Process old data if it's a dictionary
        if isinstance(old_data, dict):
            for timestamp, entry in old_data.items():
                # Skip if entry is not a dictionary
                if not isinstance(entry, dict):
                    continue
                    
                # Extract top3 if it exists
                if "top3" in entry:
                    new_data["priorities"].append({
                        "time": timestamp,
                        "text": entry["top3"]
                    })
                
                # Always add the action
                new_data["actions"].append({
                    "time": timestamp,
                    "past_15": entry.get("past_15", ""),
                    "next_15": entry.get("next_15", "")
                })
        # If it's already in the new format, just return it
        elif isinstance(old_data, dict) and "priorities" in old_data and "actions" in old_data:
            return old_data
        # If it's something else entirely, just return the default empty structure
        
        return new_data

    def get_latest_top3(self):
        """Get the most recent top 3 priorities from entries"""
        # Default empty value
        latest_top3 = ""
        
        # Check if we have any priorities
        if "priorities" in self.data and self.data["priorities"]:
            # First, sort priorities by timestamp (newest first)
            sorted_by_time = sorted(self.data["priorities"], 
                                   key=lambda x: x.get("time", ""), 
                                   reverse=True)
            
            # Get the most recent timestamp
            if sorted_by_time:
                latest_time = sorted_by_time[0].get("time", "")
                
                # Find all priorities with this timestamp
                latest_priorities = [p for p in sorted_by_time if p.get("time", "") == latest_time]
                
                # If there are multiple entries with the same timestamp, use the last one
                # (which would be the last one added to the JSON file)
                if latest_priorities:
                    # Use the last one in the original list (not the sorted list)
                    # This ensures we get the last one that was added
                    for priority in reversed(self.data["priorities"]):
                        if priority.get("time", "") == latest_time:
                            latest_top3 = priority.get("text", "")
                            break
                
        return latest_top3

    def save_data(self):
        """Save current data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)

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
        # If a window already exists, destroy it to create a fresh one
        if self.window is not None and self.window.winfo_exists():
            print("Destroying existing window to create a new one")
            self.window.destroy()
            self.window = None

        # Record the timestamp when the popup is initiated - always use current time
        self.current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
        self.window = tk.Toplevel(self.root)
        self.window.title("Productivity Check")
        self.window.geometry("400x400")  # Increased height for new field
        
        # Make window resizable
        self.window.resizable(True, True)
        
        # Make window always on top initially
        self.window.attributes('-topmost', True)
        
        # Show in taskbar (remove the toolwindow attribute)
        # No need to withdraw and deiconify since we want it to show in taskbar
        
        # Handle window close event to minimize instead of close
        self.window.protocol("WM_DELETE_WINDOW", self.minimize_window)
        
        # Bind to <Map> event (window becomes visible) to update time
        # This event occurs when the window is restored from minimized state
        self.window.bind("<Map>", lambda e: self.update_time_label())
        
        # Center the window on screen
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        # Set window icon (optional)
        try:
            # Create a simple icon
            icon = Image.new("RGBA", (32, 32), color=(0, 120, 215))
            draw = ImageDraw.Draw(icon)
            draw.rectangle([(8, 8), (24, 24)], fill=(255, 255, 255))
            photo = ImageTk.PhotoImage(icon)
            self.window.iconphoto(True, photo)
        except Exception as e:
            print(f"Error setting icon: {e}")

        # Configure the main frame to expand
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(2, weight=1)  # Top 3 row (now at top)
        self.window.grid_rowconfigure(4, weight=1)  # Past entry row
        self.window.grid_rowconfigure(6, weight=1)  # Next entry row

        # Current time label - update with fresh current time including seconds
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label = tk.Label(self.window, text=f"Time: {current_time}", font=("Arial", 12))
        self.time_label.grid(row=0, column=0, pady=10)

        # Top 3 priorities field (moved to top)
        top3_label = tk.Label(self.window, text="Your top 3 current priorities:", font=("Arial", 10, "bold"))
        top3_label.grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.top3_entry = tk.Text(self.window, height=4, width=40)
        self.top3_entry.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # Load the most recent top 3 priorities
        latest_top3 = self.get_latest_top3()
        if latest_top3:
            self.top3_entry.insert("1.0", latest_top3)

        # Past 15 minutes question
        past_label = tk.Label(self.window, text="What did you get done in the past 15 minutes?")
        past_label.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.past_entry = tk.Text(self.window, height=4, width=40)
        self.past_entry.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)

        # Next 15 minutes question
        next_label = tk.Label(self.window, text="What's your aim for the next 15 minutes?")
        next_label.grid(row=5, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.next_entry = tk.Text(self.window, height=4, width=40)
        self.next_entry.grid(row=6, column=0, sticky="nsew", padx=10, pady=5)

        # Button frame for Submit and Quit buttons
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=7, column=0, pady=10)
        
        # Submit button
        self.submit_button = tk.Button(button_frame, text="Submit", command=self.submit)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Set tab order - start with top3 now
        self.top3_entry.focus_set()
        
        # Override tab behavior
        self.top3_entry.bind("<Tab>", self.focus_next_widget)
        self.past_entry.bind("<Tab>", self.focus_next_widget)
        self.next_entry.bind("<Tab>", self.focus_next_widget)
        self.submit_button.bind("<Tab>", self.focus_next_widget)

    def focus_next_widget(self, event):
        """Move focus to next widget when Tab is pressed"""
        event.widget.tk_focusNext().focus()
        return "break"  # Prevents the default Tab behavior
        
    def submit(self, minimize=True):
        """Handle form submission"""
        # Use the timestamp from when the popup was initiated
        past_text = self.past_entry.get("1.0", tk.END).strip()
        next_text = self.next_entry.get("1.0", tk.END).strip()
        top3_text = self.top3_entry.get("1.0", tk.END).strip()
        
        # Get the most recent top3 value to compare
        latest_top3 = self.get_latest_top3()
        
        # Always add an action entry
        self.data["actions"].append({
            "time": self.current_timestamp,
            "past_15": past_text,
            "next_15": next_text
        })
        
        # Only add a priority entry if the top3 text has changed
        if top3_text != latest_top3:
            self.data["priorities"].append({
                "time": self.current_timestamp,
                "text": top3_text
            })
        
        self.save_data()
        
        # Clear the text fields except top3
        if self.window.winfo_exists():
            self.past_entry.delete("1.0", tk.END)
            self.next_entry.delete("1.0", tk.END)
            
            # Minimize the window if requested
            if minimize:
                self.window.iconify()  # Minimize the window

    def on_closing(self):
        """Handle window closing event"""
        # Save current data
        self.submit()
        
    def minimize_window(self):
        """Minimize the window instead of closing it"""
        print("Minimizing window instead of closing")  # Debug print
        if self.window is not None and self.window.winfo_exists():
            self.window.iconify()  # Minimize the window
            
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
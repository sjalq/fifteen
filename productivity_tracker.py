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
import pystray
from pystray import MenuItem as item
import ctypes
# Comment out problematic imports
# import win32gui
# import win32con

class ProductivityApp:
    def __init__(self):
        # Set custom Windows AppID to override default Python taskbar icon
        try:
            myappid = u'productivitytracker.main.app.1.0'  # Unique AppID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            print("Windows AppID set for custom taskbar icon")
        except Exception as e:
            print(f"Could not set Windows AppID: {e}")
            
        self.window = None
        self.running = True
        self.data_file = "productivity_log.json"
        self.data = self.load_existing_data()
        self.popup_queue = queue.Queue()
        self.last_active = True
        # Store timestamp when popup is shown
        self.current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create root window but keep it hidden
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Create system tray icon
        print("Creating tray icon...")  # Debug
        self.create_tray_icon()
        print("Tray icon created successfully")  # Debug
        
        # Start the timer in a separate thread
        self.timer_thread = threading.Thread(target=self.schedule_popup)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        # Don't show popup immediately - only on timer or manual tray click
        
        # Check queue periodically for popup requests
        self.root.after(1000, self.check_popup_queue)
        
        # Start the tray icon in a separate thread after a small delay
        def start_tray():
            print("Starting tray icon thread...")  # Debug
            time.sleep(0.5)  # Small delay to ensure tkinter is ready
            print("Running tray icon...")  # Debug
            self.icon.run()
            print("Tray icon stopped")  # Debug
            
        self.tray_thread = threading.Thread(target=start_tray)
        self.tray_thread.daemon = True
        self.tray_thread.start()
        
        # Start the tkinter main loop on the main thread
        self.root.mainloop()
        
    def create_tray_icon(self):
        """Create the system tray icon"""
        # Try to load existing icon, otherwise create a simple one
        try:
            if os.path.exists("icon.ico"):
                self.icon_image = Image.open("icon.ico")
            else:
                # Create a simple icon if file doesn't exist
                self.icon_image = Image.new("RGBA", (64, 64), color=(0, 120, 215))
                draw = ImageDraw.Draw(self.icon_image)
                draw.rectangle([(16, 16), (48, 48)], fill=(255, 255, 255))
        except Exception as e:
            # Fallback to a simple colored square
            self.icon_image = Image.new("RGBA", (64, 64), color=(0, 120, 215))
        
        # Create menu items using pystray's default Windows behavior:
        # - Right-click shows menu
        # - Left-click triggers the DEFAULT menu item
        menu = pystray.Menu(
            item('Show Popup', self.show_popup_from_menu, default=True),  # Left-click triggers this
            pystray.Menu.SEPARATOR,
            item('Quit', self.quit_application)
        )
        
        # Create the icon - let pystray handle clicks with default behavior
        self.icon = pystray.Icon("ProductivityTracker", self.icon_image, "Productivity Tracker", menu)
        
        print("Tray icon configured with Windows defaults:")
        print("- Left-click: triggers 'Show Popup' (default item)")
        print("- Right-click: shows menu")
        
    def handle_left_click_for_menu(self, icon):
        """Handle left click to show menu programmatically"""
        print("Left click detected - should show menu")
        # This might not work as expected on Windows
        pass
        
    def handle_any_click(self, icon, button=None):
        """Handle any click on tray icon"""
        print(f"CLICK detected on tray icon! Button: {button}")  # Debug
        print(f"Icon: {icon}, Button type: {type(button)}")  # More debug
        
        # For now, any click shows popup
        self.root.after(0, self.direct_show_popup)
        
    def handle_left_click(self, icon=None):
        """Handle left click on tray icon"""
        print("LEFT CLICK detected on tray icon!")  # Debug
        # For now, just show popup - you wanted right-click to show popup
        self.root.after(0, self.direct_show_popup)
        
    def handle_right_click(self, icon=None):
        """Handle right click on tray icon"""
        print("RIGHT CLICK detected on tray icon!")  # Debug
        # Show popup on right click as requested
        self.root.after(0, self.direct_show_popup)
        
    def show_popup_from_menu(self, icon=None, item=None):
        """Show/hide popup when menu item is clicked (toggle behavior)"""
        print("MENU ITEM clicked - toggling popup")  # Debug
        # Schedule the popup toggle to be shown from the main thread
        self.root.after(0, self.toggle_popup)
        
    def toggle_popup(self):
        """Toggle popup visibility - show if hidden, hide if visible"""
        print("toggle_popup called")  # Debug
        
        # Check if window exists and is visible
        if self.window is not None and self.window.winfo_exists():
            try:
                # Check if window is visible (not withdrawn)
                window_state = self.window.state()
                if window_state == 'normal' or window_state == 'zoomed':
                    # Window is visible, hide it
                    print("Window is visible, hiding it")
                    self.window.withdraw()
                    return
                else:
                    # Window exists but is hidden, show it
                    print("Window exists but hidden, showing it")
                    self.window.deiconify()
                    self.window.lift()
                    self.window.focus_force()
                    # Update timestamp and time display
                    self.current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.update_time_label()
                    return
            except:
                # If there's an error checking state, recreate window
                print("Error checking window state, recreating")
                self.window.destroy()
                self.window = None
        
        # No window exists or it was destroyed, create new one
        print("Creating new popup window")
        self.create_popup()
        
    def show_popup_from_tray(self, icon=None, item=None):
        """Show popup when tray icon is clicked (legacy)"""
        print("Legacy tray function called - scheduling popup")  # Debug
        # Schedule the popup to be shown from the main thread
        self.root.after(0, self.direct_show_popup)
        
    def quit_application(self, icon=None, item=None):
        """Quit the application from tray menu"""
        self.running = False
        # Schedule the quit on the main thread
        self.root.after(0, self._quit_main_thread)
        
    def _quit_main_thread(self):
        """Actually quit from the main thread"""
        self.icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def direct_show_popup(self):
        """Directly show the popup without going through the queue"""
        print("direct_show_popup called")  # Debug print
        
        # If window exists but is hidden, show it
        if self.window is not None and self.window.winfo_exists():
            # If window is withdrawn, bring it back
            try:
                self.window.deiconify()  # Show the window
                self.window.lift()       # Bring to front
                self.window.focus_force() # Give it focus
                # Update timestamp and time display
                self.current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.update_time_label()
                return
            except:
                # If there's an error, destroy and recreate
                self.window.destroy()
                self.window = None
            
        # Create a new popup if none exists
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
        self.quit_application()

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
            self.window.destroy()
            
        # Update timestamp when popup is created
        self.current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        self.window = tk.Toplevel(self.root)
        self.window.title("Productivity Check")
        
        # Remove focus event handling that was causing issues
        # self.window.bind("<FocusOut>", self.handle_focus_lost)
        self.last_active = True
        
        # Make window resizable
        self.window.resizable(True, True)
        
        # Make window always on top initially
        self.window.attributes('-topmost', True)
        
        # Handle window close event to minimize instead of close
        self.window.protocol("WM_DELETE_WINDOW", self.minimize_window)
        
        # Bind to <Map> event (window becomes visible) to update time
        # This event occurs when the window is restored from minimized state
        self.window.bind("<Map>", lambda e: self.update_time_label())
        
        # Add a binding to handle clicks outside the window
        self.window.bind("<Button-1>", self.handle_click)
        
        # Set window size to 1/4 horizontal and 1/2 vertical resolution of screen
        win_width = self.window.winfo_screenwidth() // 4
        win_height = self.window.winfo_screenheight() // 2
        
        # Center the window on screen
        x = (self.window.winfo_screenwidth() // 2) - (win_width // 2)
        y = (self.window.winfo_screenheight() // 2) - (win_height // 2)
        self.window.geometry(f'{win_width}x{win_height}+{x}+{y}')

        # Apply a modern theme with better font rendering
        self.window.configure(bg="#f0f0f0")
        
        # Set window icon to match tray icon (with AppID override)
        try:
            print(f"Setting window icon... Has icon_image: {hasattr(self, 'icon_image')}")
            
            # Try multiple methods for maximum compatibility
            if os.path.exists("icon.ico"):
                print("Setting icon from icon.ico file")
                # Method 1: Direct iconbitmap (most reliable on Windows)
                try:
                    self.window.iconbitmap("icon.ico")
                    self.root.iconbitmap("icon.ico")
                    print("iconbitmap set successfully")
                except Exception as e:
                    print(f"iconbitmap failed: {e}")
                
                # Method 2: Also set iconphoto for additional coverage
                try:
                    ico_image = Image.open("icon.ico")
                    if ico_image.size != (32, 32):
                        ico_image = ico_image.resize((32, 32), Image.Resampling.LANCZOS)
                    self.icon_photo = ImageTk.PhotoImage(ico_image)
                    self.root.iconphoto(False, self.icon_photo)
                    self.window.after(250, lambda: self.window.iconphoto(False, self.icon_photo))
                    print("iconphoto also set with delay")
                except Exception as e:
                    print(f"iconphoto failed: {e}")
                    
            elif hasattr(self, 'icon_image') and self.icon_image:
                print("Using icon_image from tray icon")
                window_icon = self.icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(window_icon)
                self.root.iconphoto(False, self.icon_photo)
                self.window.after(250, lambda: self.window.iconphoto(False, self.icon_photo))
                print("Window icon set from tray icon image")
                
            else:
                print("Creating fallback icon")
                icon = Image.new("RGBA", (32, 32), color=(0, 120, 215))
                draw = ImageDraw.Draw(icon)
                draw.rectangle([(8, 8), (24, 24)], fill=(255, 255, 255))
                self.icon_photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(False, self.icon_photo)
                self.window.after(250, lambda: self.window.iconphoto(False, self.icon_photo))
                print("Window icon set with fallback")
                
        except Exception as e:
            print(f"Error setting window icon: {e}")
            print(f"Exception type: {type(e).__name__}")

        # Configure the main frame to expand
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(2, weight=1)  # Top 3 row (now at top)
        self.window.grid_rowconfigure(4, weight=1)  # Past entry row
        self.window.grid_rowconfigure(6, weight=1)  # Next entry row

        # Current time label - update with fresh current time including seconds
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label = tk.Label(self.window, text=f"Time: {current_time}", font=("Segoe UI", 14), bg="#f0f0f0")
        self.time_label.grid(row=0, column=0, pady=10)

        # Top 3 priorities field (moved to top)
        top3_label = tk.Label(self.window, text="Your top 3 current priorities:", font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
        top3_label.grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.top3_entry = tk.Text(self.window, height=4, width=40, font=("Segoe UI", 11), bg="#ffffff", bd=2, relief="groove")
        self.top3_entry.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # Load the most recent top 3 priorities
        latest_top3 = self.get_latest_top3()
        if latest_top3:
            self.top3_entry.insert("1.0", latest_top3)

        # Past 15 minutes question
        past_label = tk.Label(self.window, text="What did you get done in the past 15 minutes?", font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
        past_label.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.past_entry = tk.Text(self.window, height=4, width=40, font=("Segoe UI", 11), bg="#ffffff", bd=2, relief="groove")
        self.past_entry.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)

        # Next 15 minutes question
        next_label = tk.Label(self.window, text="What's your aim for the next 15 minutes?", font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
        next_label.grid(row=5, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.next_entry = tk.Text(self.window, height=4, width=40, font=("Segoe UI", 11), bg="#ffffff", bd=2, relief="groove")
        self.next_entry.grid(row=6, column=0, sticky="nsew", padx=10, pady=5)

        # Button frame for Submit and Quit buttons
        button_frame = tk.Frame(self.window, bg="#f0f0f0")
        button_frame.grid(row=7, column=0, pady=10)
        
        # Submit button
        self.submit_button = tk.Button(
            button_frame, 
            text="Submit", 
            command=self.submit,
            bg="#4CAF50", 
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Close button (red with white text)
        self.close_button = tk.Button(
            button_frame, 
            text="Close", 
            command=self.confirm_close,
            bg="#FF5252",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=5,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.close_button.pack(side=tk.LEFT, padx=5)
        
        # Set tab order - start with top3 now
        self.top3_entry.focus_set()
        
        # Override tab behavior
        self.top3_entry.bind("<Tab>", self.focus_next_widget)
        self.past_entry.bind("<Tab>", self.focus_next_widget)
        self.next_entry.bind("<Tab>", self.focus_next_widget)
        self.submit_button.bind("<Tab>", self.focus_next_widget)
        self.close_button.bind("<Tab>", self.focus_next_widget)

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
            
            # Hide the window if requested (withdraw completely, don't just minimize)
            if minimize:
                self.window.withdraw()  # Hide the window completely

    def on_closing(self):
        """Handle window closing event"""
        # Save current data
        self.submit()
        
    def minimize_window(self):
        """Hide the window instead of closing it"""
        print("Hiding window instead of closing")  # Debug print
        if self.window is not None and self.window.winfo_exists():
            self.window.withdraw()  # Hide the window completely
            
    def hide_window(self):
        """Hide the window instead of closing it"""
        print("Hiding window instead of closing")  # Debug print
        if self.window is not None and self.window.winfo_exists():
            self.window.withdraw()

    def handle_click(self, event):
        """Handle clicks on the window"""
        # Get the widget that was clicked
        widget = event.widget
        
        # If the click was on the window itself (not its children)
        if widget == self.window:
            # Get the coordinates of the click relative to the window
            x = event.x
            y = event.y
            
            # Get the window's geometry
            width = self.window.winfo_width()
            height = self.window.winfo_height()
            
            # Only minimize if the click was outside the window's content area
            # (i.e., on the window's border or title bar)
            if x < 0 or x > width or y < 0 or y > height:
                self.window.iconify()

    def handle_focus_gained(self, event):
        """Handle when window gains focus"""
        self.last_active = True

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

    def confirm_close(self):
        """Two-step close button process"""
        try:
            if hasattr(self, 'close_button') and self.close_button.winfo_exists():
                if self.close_button["text"] == "Close":
                    self.close_button.config(text="Sure?")
                else:
                    self.close_permanently()
            else:
                # Fallback if button doesn't exist
                self.close_permanently()
        except Exception as e:
            print(f"Error in confirm_close: {e}")
            # Fallback to regular close
            self.close_permanently()

    def close_permanently(self):
        """Close the application completely, not just minimize"""
        self.quit_application()

if __name__ == "__main__":
    app = ProductivityApp()
# Python Productivity Tracker - Complete Technical Analysis

## Overview
A Windows desktop application that prompts users every 15 minutes to track their productivity by recording what they accomplished and what they plan to do next. The app runs in the system tray and integrates with Todoist for priority management.

## Core Architecture

### Main Components

1. **ProductivityApp Class** (productivity_tracker.py)
   - Main application controller
   - Manages GUI, system tray, timer, and data persistence
   - Handles all user interactions and system events

### Key Features

#### 1. System Tray Integration
- **Icon**: Blue background (RGB: 0, 120, 215) with white square in center
- **Left-click behavior**: Shows popup (default menu item)
- **Right-click behavior**: Shows context menu
- **Menu items**:
  - "Show Popup" (default, triggered by left-click)
  - Separator
  - "Timer: ON/OFF" (toggle with checkmark)
  - Separator
  - "Quit"

#### 2. Timer System
- **15-minute intervals**: Triggers at exact times (:00, :15, :30, :45)
- **Timer thread**: Separate daemon thread running schedule_popup()
- **Toggle functionality**: Can be disabled/enabled via tray menu
- **Persistence**: Timer state saved in JSON settings

#### 3. Popup Window
- **Size**: 1/4 screen width × 1/2 screen height
- **Position**: Centered on screen
- **Always on top**: Initially set to topmost
- **Pre-created**: Window created at startup, hidden until needed
- **Minimize behavior**: 
  - When minimized: Submits data and withdraws from taskbar
  - Window completely hidden (not just minimized)
  
#### 4. Window Components (Top to Bottom)
1. **Time Label**: Shows current time (HH:MM:SS format)
2. **Top 3 Priorities Text Area**: 
   - Multi-line text input
   - Persists across sessions
   - Only saves when changed
3. **Past 15 Minutes Text Area**: 
   - "What did you get done in the past 15 minutes?"
   - Clears after submission
4. **Next 15 Minutes Text Area**:
   - "What's your aim for the next 15 minutes?"
   - Clears after submission
5. **Button Row**:
   - Submit (Green #4CAF50)
   - Play Video (Blue #2196F3)
   - Sync Todoist (Orange #FF9800)
   - Close (Red #FF5252)

#### 5. Data Persistence
- **File**: productivity_log.json
- **Format**:
```json
{
    "priorities": [
        {"time": "2025-03-13 10:13", "text": "priority text"}
    ],
    "actions": [
        {
            "time": "2025-03-13 10:13",
            "past_15": "what was done",
            "next_15": "what will be done"
        }
    ],
    "settings": {
        "timer_enabled": true
    }
}
```
- **Migration**: Supports migrating from old format automatically
- **Backup**: Creates timestamped backup before migration

#### 6. Todoist Integration
- **API Token**: Hardcoded "0f3ea04ceb24e895b8bb85b5323347d44d06fd27"
- **Sync Interval**: 24 hours automatic
- **Manual Sync**: Via button in popup
- **Priority Tasks**: Fetches Priority 1 tasks (API priority=4)
- **Format**: Bullet points with "* " prefix
- **Threading**: Async background sync

#### 7. Video Player
- **File**: "Top 3 things.mp4"
- **Behavior**: Minimizes app window before playing
- **Player**: Uses Windows default (os.startfile)

#### 8. Window Icon Management
- **AppID**: Sets custom Windows AppUserModelID
- **Icon Loading**: Multiple methods for compatibility
- **Fallback**: Creates blue/white icon if file missing

#### 9. Close Button Behavior
- **Two-step process**: "Close" → "Sure?" → Actually close
- **Prevents accidental closure**

#### 10. Focus Management
- **Tab Order**: top3 → past → next → buttons
- **Auto-focus**: top3_entry gets focus when popup shows
- **Window State Tracking**: Handles Map/Unmap events

#### 11. Window Resizing
- **Resizable**: Window can be resized by user
- **Grid Layout**: Uses grid with weight configuration for proper scaling
- **Column/Row Weights**: Expands text areas proportionally

#### 12. Data Entry Timestamps
- **Timestamp Capture**: Set when popup is created/shown, NOT when submitted
- **Consistent Timing**: All entries in a submission use same timestamp
- **Format**: "%Y-%m-%d %H:%M:%S" (e.g., "2025-03-13 10:13:07")

#### 13. Startup Sequence
1. Set Windows AppUserModelID for taskbar icon
2. Initialize data structures and load JSON
3. Create hidden root window
4. Pre-create popup window (hidden)
5. Start timer thread
6. Lazy load heavy imports in background
7. Create system tray icon after 100ms delay
8. Begin main event loop

#### 14. Menu State Updates
- **Dynamic Menu Text**: "Timer: ON" or "Timer: OFF" based on state
- **Checkmark**: Shows checked state for timer toggle
- **Menu Recreation**: Rebuilds menu when timer state changes

#### 15. Todoist Button Behavior
- **Button Text Change**: Shows "Syncing..." during operation
- **Text Reset**: Returns to "Sync Todoist" after 1 second
- **Field Update**: Populates top3_entry with fetched tasks
- **Background Execution**: Runs in separate thread

## Technical Implementation Details

### Threading Model
- **Main Thread**: Tkinter GUI event loop
- **Timer Thread**: Daemon thread for 15-minute scheduling
- **Tray Thread**: Daemon thread for pystray icon
- **Sync Thread**: On-demand threads for Todoist API calls

### Lazy Loading
- Heavy imports (PIL, pystray, requests) loaded after GUI initialization
- Improves startup time
- Delayed tray setup (100ms after startup)

### Window Management
- Root window always hidden (self.root.withdraw())
- Popup window pre-created but hidden
- Efficient show/hide instead of create/destroy
- Handles window state transitions properly

### Error Handling
- Try/except blocks around critical operations
- Fallback icon creation if file missing
- Graceful handling of API failures
- Window state verification before operations

### Performance Optimizations
- Pre-created popup window
- Efficient JSON operations
- Minimal UI updates
- Smart timer sleep calculations

## External Dependencies
- **tkinter**: GUI framework (included with Python)
- **PIL/Pillow**: Image processing for icons
- **pystray**: System tray functionality  
- **requests**: HTTP client for Todoist API
- **pywin32**: Windows-specific features (in requirements but commented out in code)
- **ctypes**: Windows API calls (built-in)

## Build Process
- **PyInstaller**: Creates single executable
- **No console**: --noconsole flag
- **Icon**: Embeds icon.ico
- **Single file**: All dependencies bundled

## File Structure
```
fifteen/
├── productivity_tracker.py      # Main application
├── productivity_tracker_fast.py # Simplified version
├── icon.py                      # Icon generator
├── icon.ico                     # Application icon
├── productivity_log.json        # Data storage
├── Top 3 things.mp4            # Video file
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
└── productivity_tracker.spec   # PyInstaller config
```

## Critical Behaviors to Preserve

1. **Exact 15-minute intervals** - Must trigger at :00, :15, :30, :45
2. **Window minimize = submit + hide** - Not just minimize to taskbar
3. **Tray icon click behaviors** - Left = show, Right = menu
4. **Two-step close confirmation** - Prevents accidents
5. **Timestamp handling** - Uses popup creation time, not submit time
6. **Priority deduplication** - Only saves if changed
7. **Focus management** - Proper tab order and auto-focus
8. **Thread safety** - UI updates via root.after()
9. **JSON format compatibility** - Must match existing structure
10. **Todoist sync format** - Bullet points with "* " prefix
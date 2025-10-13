# Rust Implementation Tickets

## Epic 1: Core Application Setup

### Ticket 1.1: Initialize Rust Project Structure
**Priority**: High
**Description**: Set up the basic Rust project with Windows-specific configurations and dependencies.

**Definition of Done**:
- Cargo.toml exists with all required dependencies
- Project compiles with `cargo build`
- Windows executable settings configured
- Icon resource configuration present

**Dependencies**:
```toml
[dependencies]
winit = "0.29"
tray-icon = "0.13"
egui = "0.27"
eframe = "0.27"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = "0.4"
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", features = ["json"] }
windows = { version = "0.54", features = ["Win32_UI_Shell", "Win32_System_LibraryLoader"] }
image = "0.24"
embed-resource = "2.4"
```

### Ticket 1.2: Create Icon Generation and Embedding
**Priority**: High
**Description**: Generate the blue/white icon and embed it into the executable.

**Definition of Done**:
- Icon.ico generated with blue background (RGB: 0,120,215) and white square
- Icon embedded in .exe and visible in Windows Explorer
- Application manifest configured

**Files**: `build.rs`, `src/icon.rs`

## Epic 2: System Tray Implementation

### Ticket 2.1: Basic System Tray Icon
**Priority**: High
**Description**: Implement system tray icon with basic visibility.

**Definition of Done**:
- Icon visible in system tray when app runs
- Tooltip shows "Productivity Tracker" on hover
- Icon persists until app closes

**Files**: `src/tray.rs`

### Ticket 2.2: Tray Menu and Click Handling
**Priority**: High
**Description**: Implement the complete tray menu with all interactions.

**Definition of Done**:
- Left-click on tray icon shows popup
- Right-click shows menu with: "Show Popup" | --- | "Timer: ON/OFF" | --- | "Quit"
- All menu items functional
- Timer toggle updates menu text

**Files**: `src/tray.rs`, `src/menu.rs`

## Epic 3: GUI Window Implementation

### Ticket 3.1: Main Window Setup
**Priority**: High
**Description**: Create the main popup window with proper sizing and positioning.

**Definition of Done**:
- Window appears at 1/4 screen width × 1/2 screen height
- Window centered on screen
- Window stays on top initially
- Windows AppUserModelID set
- Window resizable

**Files**: `src/gui/window.rs`

### Ticket 3.2: Window Layout and Components
**Priority**: High
**Description**: Implement all UI components in the correct layout.

**Definition of Done**:
- Time label shows HH:MM:SS at top
- Three text areas with correct labels
- Four buttons with correct colors: Submit (#4CAF50), Play Video (#2196F3), Sync Todoist (#FF9800), Close (#FF5252)
- Layout scales properly when resized

**Files**: `src/gui/components.rs`

### Ticket 3.3: Window Behavior and State Management
**Priority**: Medium
**Description**: Implement window show/hide behavior and state tracking.

**Definition of Done**:
- Window pre-created at startup but hidden
- Show/hide reuses same window instance
- Minimize triggers submit + complete withdrawal from taskbar
- Tab order: top3 → past → next → buttons
- Top3 field auto-focused on show

**Files**: `src/gui/window_state.rs`

## Epic 4: Data Persistence

### Ticket 4.1: JSON Data Model
**Priority**: High
**Description**: Define data structures matching the Python JSON format.

**Definition of Done**:
- Structs serialize/deserialize to exact Python JSON format
- Test file loads and saves correctly
- Format matches: {"priorities": [...], "actions": [...], "settings": {...}}

**Files**: `src/data/models.rs`

### Ticket 4.2: File Operations
**Priority**: High
**Description**: Implement loading and saving of productivity_log.json.

**Definition of Done**:
- Loads existing productivity_log.json on startup
- Creates file if missing with default structure
- Saves with 4-space indentation
- Preserves timestamp format: "YYYY-MM-DD HH:MM:SS"

**Files**: `src/data/persistence.rs`

## Epic 5: Timer System

### Ticket 5.1: 15-Minute Timer Implementation
**Priority**: High
**Description**: Create the timer that triggers at exact 15-minute intervals.

**Definition of Done**:
- Popup appears at :00, :15, :30, :45 exactly
- Timer runs in background thread
- Respects timer_enabled setting
- Efficient sleep between checks

**Files**: `src/timer.rs`

### Ticket 5.2: Timer Toggle Functionality
**Priority**: Medium
**Description**: Allow enabling/disabling timer via tray menu.

**Definition of Done**:
- Menu shows "Timer: ON" or "Timer: OFF"
- Toggle persists to settings in JSON
- Timer stops/starts immediately on toggle
- Checkmark shows current state

**Files**: `src/timer.rs`, `src/tray.rs`

## Epic 6: Form Submission Logic

### Ticket 6.1: Data Collection and Validation
**Priority**: High
**Description**: Handle form submission with proper data collection.

**Definition of Done**:
- Submit captures all three text fields
- Timestamp set when popup shown (not submit time)
- Past/next fields cleared after submit
- Top3 field retained
- Window hides after submit

**Files**: `src/gui/form.rs`

### Ticket 6.2: Smart Priority Saving
**Priority**: Medium
**Description**: Only save priorities when they change.

**Definition of Done**:
- Priority entry only added if text differs from last saved
- Action entry always added
- Whitespace-only entries handled correctly

**Files**: `src/data/logic.rs`

## Epic 7: Todoist Integration

### Ticket 7.1: API Client Setup
**Priority**: Medium
**Description**: Create Todoist API client with hardcoded token.

**Definition of Done**:
- API client connects to Todoist with hardcoded token: "0f3ea04ceb24e895b8bb85b5323347d44d06fd27"
- Async runtime configured
- Network errors handled gracefully

**Files**: `src/todoist/client.rs`

### Ticket 7.2: Priority Task Fetching
**Priority**: Medium
**Description**: Fetch and format Priority 1 tasks from Todoist.

**Definition of Done**:
- Fetches tasks with priority=4 from Todoist API
- Returns top 3 tasks sorted by created_at
- Formats as "* Task content" with newlines between

**Files**: `src/todoist/tasks.rs`

### Ticket 7.3: Sync Functionality
**Priority**: Medium
**Description**: Implement manual and automatic Todoist sync.

**Definition of Done**:
- Button click triggers manual sync
- Auto-sync every 24 hours
- Button shows "Syncing..." during operation
- Top3 field updated with results
- Runs async without blocking UI

**Files**: `src/todoist/sync.rs`

## Epic 8: Additional Features

### Ticket 8.1: Video Player Integration
**Priority**: Low
**Description**: Play "Top 3 things.mp4" when button clicked.

**Definition of Done**:
- Plays "Top 3 things.mp4" if exists
- Window minimizes before playing
- Uses Windows default player
- Shows error if file missing

**Files**: `src/features/video.rs`

### Ticket 8.2: Close Button Two-Step Confirmation
**Priority**: Low
**Description**: Implement "Close" → "Sure?" behavior.

**Definition of Done**:
- First click changes button to "Sure?"
- Second click quits application
- Clicking elsewhere resets to "Close"

**Files**: `src/gui/components.rs`

## Epic 9: Build and Distribution

### Ticket 9.1: Single Executable Build
**Priority**: High
**Description**: Configure build to produce single .exe file.

**Definition of Done**:
- `cargo build --release` produces single .exe
- No console window appears
- Icon embedded and visible
- File size optimized (<10MB)

**Files**: `Cargo.toml`, `build.rs`

### Ticket 9.2: Asset Embedding
**Priority**: Medium
**Description**: Ensure icon and resources are embedded properly.

**Definition of Done**:
- Icon visible in Windows Explorer
- Icon shows in taskbar when running
- Works on clean Windows 10/11 system

**Files**: `build.rs`

## Epic 10: Polish and Edge Cases

### Ticket 10.1: Error Handling and Resilience
**Priority**: Medium
**Description**: Handle all edge cases gracefully.

**Definition of Done**:
- App continues running if video missing
- App works offline (Todoist failures don't crash)
- Handles read-only productivity_log.json
- No panic on any user action

**Files**: All modules

### Ticket 10.2: Performance Optimization
**Priority**: Low
**Description**: Ensure fast startup and responsive UI.

**Definition of Done**:
- Startup to tray icon <1 second
- Window show/hide <100ms
- Memory usage <50MB
- No UI freezes

**Files**: Various

## Implementation Order

1. **Phase 1** (Core): Tickets 1.1, 1.2, 3.1, 4.1, 4.2
2. **Phase 2** (Tray): Tickets 2.1, 2.2  
3. **Phase 3** (GUI): Tickets 3.2, 3.3, 6.1, 6.2
4. **Phase 4** (Timer): Tickets 5.1, 5.2
5. **Phase 5** (Features): Tickets 7.1, 7.2, 7.3, 8.1, 8.2
6. **Phase 6** (Polish): Tickets 9.1, 9.2, 10.1, 10.2

## Testing Requirements

Each ticket should include:
- Unit tests for data models and logic
- Integration tests for file I/O
- Manual testing on Windows 10/11
- Verification of exact behavior match with Python version
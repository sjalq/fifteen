# Fifteen Rust - Productivity Tracker

A Windows desktop productivity tracking application written in Rust. This is a port of the original Python implementation with full feature parity.

## Features

- System tray integration with custom icon
- 15-minute interval popups at exact times (:00, :15, :30, :45)
- Tracks top 3 priorities, past accomplishments, and next goals
- Todoist integration for syncing Priority 1 tasks
- Video player for motivational content
- Data persistence in JSON format
- Single executable distribution

## Building

### Prerequisites
- Rust 1.75 or later
- Windows 10/11

### Build Instructions

```bash
# Debug build
cargo build

# Release build (optimized single executable)
cargo build --release
```

The executable will be in `target/release/productivity_tracker.exe`

## Architecture

See `docs/PYTHON_PROJECT_ANALYSIS.md` for complete feature documentation and `docs/RUST_IMPLEMENTATION_TICKETS.md` for implementation details.

## Project Structure

```
fifteen-rust/
├── src/
│   ├── main.rs           # Entry point
│   ├── tray.rs          # System tray implementation
│   ├── gui/             # GUI components
│   ├── data/            # Data models and persistence
│   ├── timer.rs         # Timer system
│   ├── todoist/         # Todoist integration
│   └── features/        # Additional features
├── assets/              # Resources (icons, etc.)
├── docs/               # Documentation
├── Cargo.toml          # Project configuration
└── build.rs            # Build script
```
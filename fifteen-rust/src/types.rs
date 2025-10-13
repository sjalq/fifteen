use std::sync::Arc;
use chrono::{DateTime, Local};
use iced::widget::text_editor;
use iced::{Color, Theme, Border};
use iced::widget::container;
use iced::widget::button;
use serde::{Deserialize, Serialize};
use crate::{data, tray};

// ============================================================================
// APPLICATION MESSAGES
// ============================================================================

/// All possible messages/events in the application
#[derive(Debug, Clone)]
pub enum Message {
    // Window lifecycle
    ShowWindow,
    HideWindow,

    // Form inputs - using text_editor
    Top3Action(text_editor::Action),
    Past15Action(text_editor::Action),
    Next15Action(text_editor::Action),

    // Actions
    Submit,
    PlayVideo,
    SyncTodoist,
    TodoistSynced(Result<String, String>),

    // Close button
    CloseClicked,

    // Timer
    TimerTicked,
    ToggleTimer,

    // Tray
    TrayEvent(TrayCommand),
    CheckTrayEvents,

    // System
    Quit,
}

// ============================================================================
// TRAY TYPES
// ============================================================================

/// Commands that can be sent from the system tray
#[derive(Debug, Clone)]
pub enum TrayCommand {
    ToggleWindow,  // Toggle window visibility (show/hide)
    ToggleTimer,
    Quit,
}

// ============================================================================
// DATA MODEL TYPES
// ============================================================================

/// Main data structure matching Python JSON format
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductivityLog {
    pub priorities: Vec<PriorityEntry>,
    pub actions: Vec<ActionEntry>,
    pub settings: Settings,
}

/// Priority entry with timestamp and text
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriorityEntry {
    pub time: String, // Format: "YYYY-MM-DD HH:MM:SS"
    pub text: String,
}

/// Action entry with past and next 15 minutes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionEntry {
    pub time: String, // Format: "YYYY-MM-DD HH:MM:SS"
    pub past_15: String,
    pub next_15: String,
}

/// Application settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub timer_enabled: bool,
    #[serde(default)]
    pub last_todoist_sync: Option<i64>,  // Unix timestamp of last sync
}

impl Default for ProductivityLog {
    fn default() -> Self {
        Self {
            priorities: Vec::new(),
            actions: Vec::new(),
            settings: Settings::default(),
        }
    }
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            timer_enabled: true,
            last_todoist_sync: None,
        }
    }
}

// ============================================================================
// APPLICATION STATE
// ============================================================================

/// Main application state
pub struct State {
    // Window state
    pub window_visible: bool,
    pub window_id: iced::window::Id,
    pub timestamp: DateTime<Local>,

    // Form state - using text_editor for multiline
    pub top3_content: text_editor::Content,
    pub past_15_content: text_editor::Content,
    pub next_15_content: text_editor::Content,

    // UI state
    pub close_confirmation: bool,
    pub todoist_syncing: bool,

    // App state
    pub timer_enabled: bool,
    pub persistence: Arc<data::PersistenceManager>,
    pub tray_manager: Option<tray::TrayManager>,
}

impl State {
    pub fn new() -> Self {
        // Initialize persistence
        let persistence = Arc::new(
            data::PersistenceManager::new()
                .expect("Failed to initialize persistence")
        );

        let timer_enabled = persistence.is_timer_enabled();
        let top3_text = persistence.get_last_priority();

        // Initialize tray icon
        let tray_manager = tray::TrayManager::new().ok();

        Self {
            window_visible: false,
            window_id: iced::window::Id::unique(),
            timestamp: Local::now(),
            top3_content: text_editor::Content::with_text(&top3_text),
            past_15_content: text_editor::Content::new(),
            next_15_content: text_editor::Content::new(),
            close_confirmation: false,
            todoist_syncing: false,
            timer_enabled,
            persistence,
            tray_manager,
        }
    }

    pub fn submit_data(&mut self) {
        let timestamp = self.timestamp;
        let top3_text = self.top3_content.text();
        let past_15_text = self.past_15_content.text();
        let next_15_text = self.next_15_content.text();

        let _ = self.persistence.update_log(|log| {
            // Add priority if changed
            if !top3_text.trim().is_empty() {
                log.add_priority(top3_text.to_string(), timestamp);
            }

            // Add action
            if !past_15_text.trim().is_empty() || !next_15_text.trim().is_empty() {
                log.add_action(
                    past_15_text.to_string(),
                    next_15_text.to_string(),
                    timestamp,
                );
            }
        });

        // Clear past and next fields
        self.past_15_content = text_editor::Content::new();
        self.next_15_content = text_editor::Content::new();
        self.close_confirmation = false;
    }
}

// ============================================================================
// UI STYLE TYPES
// ============================================================================

/// Custom button styles matching Python colors
#[derive(Debug, Clone, Copy)]
pub enum ButtonStyle {
    Submit,      // #4CAF50 green
    PlayVideo,   // #2196F3 blue
    Todoist,     // #FF9800 orange
    Close,       // #FF5252 red
}

impl button::StyleSheet for ButtonStyle {
    type Style = Theme;

    fn active(&self, _style: &Self::Style) -> button::Appearance {
        let bg_color = match self {
            ButtonStyle::Submit => Color::from_rgb(0x4C as f32 / 255.0, 0xAF as f32 / 255.0, 0x50 as f32 / 255.0),
            ButtonStyle::PlayVideo => Color::from_rgb(0x21 as f32 / 255.0, 0x96 as f32 / 255.0, 0xF3 as f32 / 255.0),
            ButtonStyle::Todoist => Color::from_rgb(0xFF as f32 / 255.0, 0x98 as f32 / 255.0, 0x00 as f32 / 255.0),
            ButtonStyle::Close => Color::from_rgb(0xFF as f32 / 255.0, 0x52 as f32 / 255.0, 0x52 as f32 / 255.0),
        };

        button::Appearance {
            background: Some(iced::Background::Color(bg_color)),
            text_color: Color::WHITE,
            border: Border {
                radius: 2.0.into(),
                width: 2.0,
                color: bg_color,
            },
            ..Default::default()
        }
    }

    fn hovered(&self, style: &Self::Style) -> button::Appearance {
        let mut appearance = self.active(style);
        if let Some(iced::Background::Color(color)) = appearance.background {
            // Slightly darken on hover
            appearance.background = Some(iced::Background::Color(Color {
                r: color.r * 0.9,
                g: color.g * 0.9,
                b: color.b * 0.9,
                a: color.a,
            }));
        }
        appearance
    }
}

/// Container style for background color matching Python
pub struct ContainerStyle;

impl container::StyleSheet for ContainerStyle {
    type Style = Theme;

    fn appearance(&self, _style: &Self::Style) -> container::Appearance {
        container::Appearance {
            background: Some(iced::Background::Color(Color::from_rgb(
                0xF0 as f32 / 255.0,
                0xF0 as f32 / 255.0,
                0xF0 as f32 / 255.0,
            ))),
            ..Default::default()
        }
    }
}

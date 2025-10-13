use chrono::{DateTime, Local};
use crate::types::{ProductivityLog, PriorityEntry, ActionEntry};

impl ProductivityLog {
    /// Create a new empty log with default settings
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a priority entry if it differs from the last one
    pub fn add_priority(&mut self, text: String, timestamp: DateTime<Local>) {
        // Only add if text is different from last priority
        let should_add = self.priorities.is_empty()
            || self.priorities.last().map_or(true, |last| last.text != text);

        if should_add && !text.trim().is_empty() {
            self.priorities.push(PriorityEntry {
                time: format_timestamp(timestamp),
                text,
            });
        }
    }

    /// Add an action entry
    pub fn add_action(&mut self, past_15: String, next_15: String, timestamp: DateTime<Local>) {
        // Always add action entries
        self.actions.push(ActionEntry {
            time: format_timestamp(timestamp),
            past_15,
            next_15,
        });
    }

    /// Get the last priority text or empty string
    pub fn get_last_priority(&self) -> String {
        self.priorities
            .last()
            .map(|p| p.text.clone())
            .unwrap_or_default()
    }

    /// Toggle timer state
    pub fn toggle_timer(&mut self) -> bool {
        self.settings.timer_enabled = !self.settings.timer_enabled;
        self.settings.timer_enabled
    }

    /// Check if timer is enabled
    pub fn is_timer_enabled(&self) -> bool {
        self.settings.timer_enabled
    }

    /// Check if Todoist sync is needed (every 24 hours)
    pub fn should_sync_todoist(&self) -> bool {
        match self.settings.last_todoist_sync {
            None => true,  // Never synced
            Some(last_sync) => {
                let now = chrono::Utc::now().timestamp();
                let seconds_since_sync = now - last_sync;
                seconds_since_sync >= 24 * 60 * 60  // 24 hours
            }
        }
    }

    /// Update last Todoist sync timestamp
    pub fn update_todoist_sync_time(&mut self) {
        self.settings.last_todoist_sync = Some(chrono::Utc::now().timestamp());
    }
}

/// Format timestamp to match Python format: "YYYY-MM-DD HH:MM:SS"
pub fn format_timestamp(dt: DateTime<Local>) -> String {
    dt.format("%Y-%m-%d %H:%M:%S").to_string()
}

/// Parse timestamp from string
pub fn parse_timestamp(s: &str) -> Option<DateTime<Local>> {
    DateTime::parse_from_str(&format!("{} +00:00", s), "%Y-%m-%d %H:%M:%S %z")
        .ok()
        .map(|dt| dt.with_timezone(&Local))
}
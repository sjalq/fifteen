use crate::types::ProductivityLog;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use chrono::Local;

const LOG_FILE: &str = "productivity_log.json";

/// Thread-safe persistence manager
pub struct PersistenceManager {
    log: Arc<Mutex<ProductivityLog>>,
    file_path: PathBuf,
}

impl PersistenceManager {
    /// Create a new persistence manager, loading existing data or creating new
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let file_path = PathBuf::from(LOG_FILE);
        let log = if file_path.exists() {
            Self::load_from_file(&file_path)?
        } else {
            ProductivityLog::new()
        };

        Ok(Self {
            log: Arc::new(Mutex::new(log)),
            file_path,
        })
    }

    /// Load ProductivityLog from JSON file
    fn load_from_file(path: &Path) -> Result<ProductivityLog, Box<dyn std::error::Error>> {
        let contents = fs::read_to_string(path)?;
        let log: ProductivityLog = serde_json::from_str(&contents)?;
        Ok(log)
    }

    /// Save current log to file with 4-space indentation
    pub fn save(&self) -> Result<(), Box<dyn std::error::Error>> {
        let log = self.log.lock().unwrap();
        let json = serde_json::to_string_pretty(&*log)?;

        // Ensure 4-space indentation (serde_json uses 2 by default)
        let json_formatted = json.lines()
            .map(|line| {
                if line.starts_with("  ") {
                    line.replacen("  ", "    ", line.len() / 2)
                } else {
                    line.to_string()
                }
            })
            .collect::<Vec<_>>()
            .join("\n");

        fs::write(&self.file_path, json_formatted)?;
        Ok(())
    }

    /// Get a clone of the current log
    pub fn get_log(&self) -> ProductivityLog {
        self.log.lock().unwrap().clone()
    }

    /// Update the log
    pub fn update_log<F>(&self, updater: F) -> Result<(), Box<dyn std::error::Error>>
    where
        F: FnOnce(&mut ProductivityLog),
    {
        let mut log = self.log.lock().unwrap();
        updater(&mut log);
        drop(log); // Release lock before saving
        self.save()
    }

    /// Create a backup of the current log file
    pub fn create_backup(&self) -> Result<PathBuf, Box<dyn std::error::Error>> {
        if self.file_path.exists() {
            let timestamp = Local::now().format("%Y%m%d_%H%M%S");
            let backup_path = self.file_path.with_file_name(
                format!("productivity_log_backup_{}.json", timestamp)
            );
            fs::copy(&self.file_path, &backup_path)?;
            Ok(backup_path)
        } else {
            Err("No file to backup".into())
        }
    }

    /// Get last priority text
    pub fn get_last_priority(&self) -> String {
        self.log.lock().unwrap().get_last_priority()
    }

    /// Check if timer is enabled
    pub fn is_timer_enabled(&self) -> bool {
        self.log.lock().unwrap().is_timer_enabled()
    }

    /// Toggle timer state
    pub fn toggle_timer(&self) -> Result<bool, Box<dyn std::error::Error>> {
        let enabled = self.update_log(|log| {
            log.toggle_timer();
        }).map(|_| self.is_timer_enabled())?;
        Ok(enabled)
    }

    /// Check if Todoist sync is needed
    pub fn should_sync_todoist(&self) -> bool {
        self.log.lock().unwrap().should_sync_todoist()
    }

    /// Update Todoist sync timestamp
    pub fn update_todoist_sync(&self) -> Result<(), Box<dyn std::error::Error>> {
        self.update_log(|log| {
            log.update_todoist_sync_time();
        })
    }
}
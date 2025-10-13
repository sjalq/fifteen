use tray_icon::{
    menu::{Menu, MenuEvent, MenuItem, PredefinedMenuItem, CheckMenuItem},
    TrayIcon, TrayIconBuilder, TrayIconEvent,
};
use std::sync::mpsc;
use crate::types::TrayCommand;

pub struct TrayManager {
    icon: TrayIcon,
    menu: Menu,
    show_popup_item: MenuItem,
    timer_item: CheckMenuItem,
    quit_item: MenuItem,
    rx: mpsc::Receiver<TrayCommand>,
    tx: mpsc::Sender<TrayCommand>,
}

impl TrayManager {
    /// Create a new tray manager
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        // Generate icon
        let icon_data = crate::icon::generate_icon_png();

        // Create menu
        let menu = Menu::new();
        let show_popup_item = MenuItem::new("Show/Hide Window", true, None);
        let separator1 = PredefinedMenuItem::separator();
        let timer_item = CheckMenuItem::new("Timer: ON", true, true, None);
        let separator2 = PredefinedMenuItem::separator();
        let quit_item = MenuItem::new("Quit", true, None);

        menu.append(&show_popup_item)?;
        menu.append(&separator1)?;
        menu.append(&timer_item)?;
        menu.append(&separator2)?;
        menu.append(&quit_item)?;

        // Create tray icon
        let icon = TrayIconBuilder::new()
            .with_menu(Box::new(menu.clone()))
            .with_tooltip("Productivity Tracker")
            .with_icon(tray_icon::Icon::from_rgba(icon_data, 32, 32)?)
            .build()?;

        // Create command channel
        let (tx, rx) = mpsc::channel();

        Ok(Self {
            icon,
            menu,
            show_popup_item,
            timer_item,
            quit_item,
            rx,
            tx,
        })
    }

    /// Get a sender for tray commands
    pub fn get_sender(&self) -> mpsc::Sender<TrayCommand> {
        self.tx.clone()
    }

    /// Process tray events
    pub fn process_events(&mut self) -> Option<TrayCommand> {
        // Check for menu events
        if let Ok(event) = MenuEvent::receiver().try_recv() {
            if event.id == self.show_popup_item.id() {
                return Some(TrayCommand::ToggleWindow);
            } else if event.id == self.timer_item.id() {
                return Some(TrayCommand::ToggleTimer);
            } else if event.id == self.quit_item.id() {
                return Some(TrayCommand::Quit);
            }
        }

        // Check for tray icon events (left click) - toggle window
        if TrayIconEvent::receiver().try_recv().is_ok() {
            return Some(TrayCommand::ToggleWindow);
        }

        // Check for commands from other threads
        if let Ok(cmd) = self.rx.try_recv() {
            return Some(cmd);
        }

        None
    }

    /// Update timer menu item
    pub fn update_timer_state(&mut self, enabled: bool) {
        let text = if enabled { "Timer: ON" } else { "Timer: OFF" };
        self.timer_item.set_text(text);
        self.timer_item.set_checked(enabled);
    }

    /// Set the default menu item (for left click)
    pub fn set_default_item(&mut self) {
        // The show popup item is the default action
        // This is handled by checking for left click events
    }
}
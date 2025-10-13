#![windows_subsystem = "windows"]

mod data;
mod icon;
mod tray;
mod types;
mod todoist;

use iced::{
    widget::{button, column, container, row, text, Space},
    window, Application, Command, Element, Settings, Subscription, Theme, Event, Length,
};
use std::time::Duration;
use chrono::{Local, Timelike};
use types::{Message, State, ButtonStyle, ContainerStyle, TrayCommand};

fn main() -> iced::Result {
    // Set Windows App User Model ID
    #[cfg(windows)]
    set_app_id();

    // Get screen size - use ~1/2 width (30% wider + 50% = 1.95x original 1/4) x 1/2 height
    let screen_size = window::Settings::default().size;
    let win_width = (screen_size.width / 4.0) * 1.95;  // 95% wider than original
    let win_height = screen_size.height / 2.0;

    ProductivityTracker::run(Settings {
        window: window::Settings {
            size: iced::Size::new(win_width.max(400.0), win_height.max(500.0)),
            position: window::Position::Centered,
            visible: false,
            decorations: true,
            transparent: false,
            level: window::Level::AlwaysOnTop,
            resizable: true,
            exit_on_close_request: false,  // Don't exit when X is clicked
            ..Default::default()
        },
        ..Default::default()
    })
}

struct ProductivityTracker {
    state: State,
}

impl Application for ProductivityTracker {
    type Executor = iced::executor::Default;
    type Message = Message;
    type Theme = Theme;
    type Flags = ();

    fn new(_flags: ()) -> (Self, Command<Message>) {
        let state = State::new();

        // Hide window from taskbar on Windows
        #[cfg(windows)]
        hide_from_taskbar(state.window_id);

        // Check if we need to sync Todoist on startup
        let should_sync = state.persistence.should_sync_todoist();
        let cmd = if should_sync {
            Command::perform(async {}, |_| Message::SyncTodoist)
        } else {
            Command::none()
        };

        (Self { state }, cmd)
    }

    fn title(&self) -> String {
        String::from("Productivity Tracker")
    }

    fn update(&mut self, message: Message) -> Command<Message> {
        match message {
            Message::ShowWindow => {
                self.state.window_visible = true;
                self.state.timestamp = Local::now();
                self.state.close_confirmation = false;  // Reset "Sure?" to "Close" when showing

                // Hide from taskbar whenever window is shown
                #[cfg(windows)]
                hide_from_taskbar(self.state.window_id);

                Command::batch(vec![
                    window::change_mode(self.state.window_id, window::Mode::Windowed),
                    window::gain_focus(self.state.window_id),
                ])
            }

            Message::HideWindow => {
                self.state.window_visible = false;
                self.state.close_confirmation = false;  // Reset "Sure?" back to "Close"
                window::change_mode(self.state.window_id, window::Mode::Hidden)
            }

            Message::Top3Action(action) => {
                self.state.top3_content.perform(action);
                Command::none()
            }

            Message::Past15Action(action) => {
                self.state.past_15_content.perform(action);
                Command::none()
            }

            Message::Next15Action(action) => {
                self.state.next_15_content.perform(action);
                Command::none()
            }

            Message::Submit => {
                self.state.submit_data();
                self.state.window_visible = false;
                self.state.close_confirmation = false;  // Reset "Sure?" back to "Close"
                window::change_mode(self.state.window_id, window::Mode::Hidden)
            }

            Message::PlayVideo => {
                self.state.window_visible = false;
                self.state.close_confirmation = false;  // Reset "Sure?" back to "Close"
                std::thread::spawn(|| {
                    // Try multiple possible locations for the video file
                    let video_paths = [
                        "Top 3 things.mp4",           // Current directory
                        "../Top 3 things.mp4",        // Parent directory
                        "../../Top 3 things.mp4",     // Two levels up (if running from target/release)
                    ];

                    for video_path in &video_paths {
                        if std::path::Path::new(video_path).exists() {
                            #[cfg(windows)]
                            {
                                // Get absolute path for better reliability
                                if let Ok(abs_path) = std::fs::canonicalize(video_path) {
                                    let _ = std::process::Command::new("cmd")
                                        .args(&["/C", "start", "", &abs_path.to_string_lossy()])
                                        .spawn();
                                }
                            }
                            break;
                        }
                    }
                });
                window::change_mode(self.state.window_id, window::Mode::Hidden)
            }

            Message::SyncTodoist => {
                self.state.todoist_syncing = true;
                Command::perform(sync_todoist_async(), Message::TodoistSynced)
            }

            Message::TodoistSynced(result) => {
                self.state.todoist_syncing = false;
                if let Ok(tasks) = result {
                    self.state.top3_content = iced::widget::text_editor::Content::with_text(&tasks);

                    // Update the last sync timestamp
                    let _ = self.state.persistence.update_todoist_sync();

                    // Save the synced tasks as a priority entry
                    let timestamp = self.state.timestamp;
                    let _ = self.state.persistence.update_log(|log| {
                        log.add_priority(tasks.clone(), timestamp);
                    });
                }
                Command::none()
            }

            Message::CloseClicked => {
                if self.state.close_confirmation {
                    return Command::perform(async {}, |_| Message::Quit);
                } else {
                    self.state.close_confirmation = true;
                    Command::none()
                }
            }

            Message::TimerTicked => {
                let mut commands = vec![];

                // Check for 15-minute popup
                if self.state.timer_enabled && !self.state.window_visible {
                    let now = Local::now();
                    let minute = now.minute();
                    if minute == 0 || minute == 15 || minute == 30 || minute == 45 {
                        commands.push(Command::perform(async {}, |_| Message::ShowWindow));
                    }
                }

                // Check for 24-hour Todoist sync
                if !self.state.todoist_syncing && self.state.persistence.should_sync_todoist() {
                    commands.push(Command::perform(async {}, |_| Message::SyncTodoist));
                }

                if commands.is_empty() {
                    Command::none()
                } else {
                    Command::batch(commands)
                }
            }

            Message::ToggleTimer => {
                self.state.timer_enabled = !self.state.timer_enabled;
                let _ = self.state.persistence.toggle_timer();
                if let Some(ref mut tray) = self.state.tray_manager {
                    tray.update_timer_state(self.state.timer_enabled);
                }
                Command::none()
            }

            Message::TrayEvent(cmd) => {
                match cmd {
                    TrayCommand::ToggleWindow => {
                        // Toggle window visibility
                        if self.state.window_visible {
                            Command::perform(async {}, |_| Message::HideWindow)
                        } else {
                            Command::perform(async {}, |_| Message::ShowWindow)
                        }
                    }
                    TrayCommand::ToggleTimer => {
                        Command::perform(async {}, |_| Message::ToggleTimer)
                    }
                    TrayCommand::Quit => {
                        Command::perform(async {}, |_| Message::Quit)
                    }
                }
            }

            Message::CheckTrayEvents => {
                if let Some(ref mut tray) = self.state.tray_manager {
                    if let Some(cmd) = tray.process_events() {
                        return Command::perform(
                            async move { cmd },
                            Message::TrayEvent
                        );
                    }
                }
                Command::none()
            }

            Message::Quit => {
                window::close(self.state.window_id)
            }
        }
    }

    fn view(&self) -> Element<'_, Message> {
        if !self.state.window_visible {
            return column![].into();
        }

        let time_str = format!("Time: {}", Local::now().format("%H:%M:%S"));

        let content = column![
            text(time_str).size(14),

            text("Your top 3 current priorities:")
                .size(12)
                .style(iced::theme::Text::Color(iced::Color::BLACK)),
            iced::widget::text_editor(&self.state.top3_content)
                .on_action(|action| Message::Top3Action(action))
                .height(100)
                .padding(5),

            text("What did you get done in the past 15 minutes?")
                .size(12)
                .style(iced::theme::Text::Color(iced::Color::BLACK)),
            iced::widget::text_editor(&self.state.past_15_content)
                .on_action(|action| Message::Past15Action(action))
                .height(100)
                .padding(5),

            text("What's your aim for the next 15 minutes?")
                .size(12)
                .style(iced::theme::Text::Color(iced::Color::BLACK)),
            iced::widget::text_editor(&self.state.next_15_content)
                .on_action(|action| Message::Next15Action(action))
                .height(100)
                .padding(5),

            row![
                button(text("Submit").style(iced::theme::Text::Color(iced::Color::WHITE)))
                    .on_press(Message::Submit)
                    .padding([8, 16])
                    .style(iced::theme::Button::custom(ButtonStyle::Submit)),

                Space::with_width(Length::Fill),

                button(text("Play Video").style(iced::theme::Text::Color(iced::Color::WHITE)))
                    .on_press(Message::PlayVideo)
                    .padding([8, 16])
                    .style(iced::theme::Button::custom(ButtonStyle::PlayVideo)),

                Space::with_width(Length::Fill),

                button(text(if self.state.todoist_syncing { "Syncing..." } else { "Sync Todoist" })
                        .style(iced::theme::Text::Color(iced::Color::WHITE)))
                    .on_press_maybe(if !self.state.todoist_syncing { Some(Message::SyncTodoist) } else { None })
                    .padding([8, 16])
                    .style(iced::theme::Button::custom(ButtonStyle::Todoist)),

                Space::with_width(Length::Fill),

                button(text(if self.state.close_confirmation { "Sure?" } else { "Close" })
                        .style(iced::theme::Text::Color(iced::Color::WHITE)))
                    .on_press(Message::CloseClicked)
                    .padding([8, 16])
                    .style(iced::theme::Button::custom(ButtonStyle::Close)),
            ],
        ]
        .spacing(5)
        .padding(10);

        container(content)
            .style(iced::theme::Container::Custom(Box::new(ContainerStyle)))
            .width(iced::Length::Fill)
            .height(iced::Length::Fill)
            .into()
    }

    fn subscription(&self) -> Subscription<Message> {
        let timer = iced::time::every(Duration::from_secs(30))
            .map(|_| Message::TimerTicked);

        let tray_check = iced::time::every(Duration::from_millis(50))
            .map(|_| Message::CheckTrayEvents);

        // Handle window events to intercept close button (X)
        // Note: X button hides to tray, only "Close" button in UI actually quits
        let window_events = iced::event::listen_with(|event, _status| {
            if let Event::Window(_id, window::Event::CloseRequested) = event {
                Some(Message::HideWindow)
            } else {
                None
            }
        });

        Subscription::batch(vec![timer, tray_check, window_events])
    }

    fn theme(&self) -> Theme {
        Theme::Light
    }
}

// Async function for Todoist sync
async fn sync_todoist_async() -> Result<String, String> {
    todoist::fetch_priority_tasks().await
}

#[cfg(windows)]
fn set_app_id() {
    use windows::Win32::UI::Shell::SetCurrentProcessExplicitAppUserModelID;
    use windows::core::PCWSTR;

    unsafe {
        let app_id = windows::core::w!("ProductivityTracker.ProductivityTracker");
        let _ = SetCurrentProcessExplicitAppUserModelID(PCWSTR::from_raw(app_id.as_ptr()));
    }
}

#[cfg(windows)]
fn hide_from_taskbar(_window_id: iced::window::Id) {
    use windows::Win32::UI::WindowsAndMessaging::{
        FindWindowW, GetWindowLongPtrW, SetWindowLongPtrW,
        GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_APPWINDOW
    };

    std::thread::spawn(|| {
        // Wait a bit for window to be created
        std::thread::sleep(std::time::Duration::from_millis(100));

        unsafe {
            // Find window by title
            let title = windows::core::w!("Productivity Tracker");
            let hwnd = FindWindowW(None, title);

            if hwnd.0 != 0 {
                // Get current extended style
                let ex_style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);

                // Add WS_EX_TOOLWINDOW and remove WS_EX_APPWINDOW to hide from taskbar
                let new_style = (ex_style | WS_EX_TOOLWINDOW.0 as isize) & !(WS_EX_APPWINDOW.0 as isize);

                SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style);
            }
        }
    });
}

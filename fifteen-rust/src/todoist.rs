use reqwest;
use serde::{Deserialize, Serialize};

const TODOIST_API_TOKEN: &str = "0f3ea04ceb24e895b8bb85b5323347d44d06fd27";
const TODOIST_API_URL: &str = "https://api.todoist.com/rest/v2/tasks";

#[derive(Debug, Deserialize, Serialize)]
pub struct TodoistTask {
    pub id: String,
    pub content: String,
    pub priority: u8,
    pub created_at: String,
}

/// Fetch priority 1 tasks from Todoist (priority 4 in API)
pub async fn fetch_priority_tasks() -> Result<String, String> {
    let client = reqwest::Client::new();

    let response = client
        .get(TODOIST_API_URL)
        .header("Authorization", format!("Bearer {}", TODOIST_API_TOKEN))
        .header("Content-Type", "application/json")
        .send()
        .await
        .map_err(|e| format!("Failed to fetch tasks: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API request failed with status: {}", response.status()));
    }

    let tasks: Vec<TodoistTask> = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Filter for priority 4 (Priority 1 in UI)
    let mut priority_tasks: Vec<&TodoistTask> = tasks
        .iter()
        .filter(|task| task.priority == 4)
        .collect();

    // Sort by creation date (most recent first)
    priority_tasks.sort_by(|a, b| b.created_at.cmp(&a.created_at));

    // Take top 3 tasks
    let top_3: Vec<String> = priority_tasks
        .iter()
        .take(3)
        .map(|task| format!("* {}", task.content))
        .collect();

    if top_3.is_empty() {
        Err("No priority 1 tasks found".to_string())
    } else {
        Ok(top_3.join("\n"))
    }
}

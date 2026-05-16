use serde::{Deserialize, Serialize};
use std::time::SystemTime;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationEvent {
    pub id: String,
    pub title: String,
    pub body: String,
    pub notification_type: NotificationType,
    pub timestamp: u64,
    pub action_url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum NotificationType {
    BuildSuccess,
    BuildFailed,
    BuildPaused,
    BuildResumed,
    BuildCancelled,
    SystemWarning,
    SystemError,
    Info,
}

impl NotificationType {
    pub fn as_str(&self) -> &str {
        match self {
            NotificationType::BuildSuccess => "build_success",
            NotificationType::BuildFailed => "build_failed",
            NotificationType::BuildPaused => "build_paused",
            NotificationType::BuildResumed => "build_resumed",
            NotificationType::BuildCancelled => "build_cancelled",
            NotificationType::SystemWarning => "system_warning",
            NotificationType::SystemError => "system_error",
            NotificationType::Info => "info",
        }
    }
}

pub struct NotificationManager;

impl NotificationManager {
    /// Send a desktop notification (Placeholder for app layer)
    pub fn send_notification(
        _title: &str,
        _body: &str,
        _notification_type: NotificationType,
    ) -> Result<(), String> {
        // Core library does not handle UI notifications directly.
        // This should be intercepted by the Tauri/CLI wrapper.
        Ok(())
    }

    /// Send build success notification
    pub fn notify_build_success(iso_path: &str, iso_size: u64) -> Result<(), String> {
        let size_mb = iso_size / 1024 / 1024;
        let body = format!(
            "Phoenix OS ISO successfully built!\n\nSize: {} MB\nLocation: {}",
            size_mb, iso_path
        );

        Self::send_notification("Build Complete", &body, NotificationType::BuildSuccess)
    }

    /// Send build failure notification
    pub fn notify_build_failed(error: &str) -> Result<(), String> {
        let body = format!("Build failed with error:\n\n{}", error);

        Self::send_notification("Build Failed", &body, NotificationType::BuildFailed)
    }

    /// Send build paused notification
    pub fn notify_build_paused(stage: &str, progress: u32) -> Result<(), String> {
        let body = format!("Build paused at {} stage\n\nProgress: {}%", stage, progress);

        Self::send_notification("Build Paused", &body, NotificationType::BuildPaused)
    }

    /// Send build resumed notification
    pub fn notify_build_resumed(stage: &str) -> Result<(), String> {
        let body = format!("Build resumed from {} stage", stage);

        Self::send_notification("Build Resumed", &body, NotificationType::BuildResumed)
    }

    /// Send build cancelled notification
    pub fn notify_build_cancelled() -> Result<(), String> {
        Self::send_notification(
            "Build Cancelled",
            "The build process has been cancelled",
            NotificationType::BuildCancelled,
        )
    }

    /// Send system warning notification
    pub fn notify_system_warning(warning: &str) -> Result<(), String> {
        Self::send_notification("System Warning", warning, NotificationType::SystemWarning)
    }

    /// Send system error notification
    pub fn notify_system_error(error: &str) -> Result<(), String> {
        Self::send_notification("System Error", error, NotificationType::SystemError)
    }

    /// Send generic info notification
    pub fn notify_info(title: &str, message: &str) -> Result<(), String> {
        Self::send_notification(title, message, NotificationType::Info)
    }

    /// Get icon path for notification type
    fn get_icon_for_type(notification_type: &NotificationType) -> &str {
        match notification_type {
            NotificationType::BuildSuccess => "success",
            NotificationType::BuildFailed => "error",
            NotificationType::BuildPaused => "warning",
            NotificationType::BuildResumed => "info",
            NotificationType::BuildCancelled => "warning",
            NotificationType::SystemWarning => "warning",
            NotificationType::SystemError => "error",
            NotificationType::Info => "info",
        }
    }

    /// Get current timestamp
    pub fn get_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0)
    }

    /// Create notification event for logging
    pub fn create_event(
        title: &str,
        body: &str,
        notification_type: NotificationType,
    ) -> NotificationEvent {
        NotificationEvent {
            id: uuid::Uuid::new_v4().to_string(),
            title: title.to_string(),
            body: body.to_string(),
            notification_type,
            timestamp: Self::get_timestamp(),
            action_url: None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_notification_type_as_str() {
        assert_eq!(NotificationType::BuildSuccess.as_str(), "build_success");
        assert_eq!(NotificationType::BuildFailed.as_str(), "build_failed");
        assert_eq!(NotificationType::SystemError.as_str(), "system_error");
    }

    #[test]
    fn test_create_notification_event() {
        let event =
            NotificationManager::create_event("Test", "Test message", NotificationType::Info);

        assert_eq!(event.title, "Test");
        assert_eq!(event.body, "Test message");
        assert_eq!(event.notification_type, NotificationType::Info);
        assert!(!event.id.is_empty());
        assert!(event.timestamp > 0);
    }
}

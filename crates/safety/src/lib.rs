use rand::{distributions::Alphanumeric, Rng};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SafetyContext {
    pub force_mode: bool,
    pub confirmation_token: Option<String>,
}

#[derive(Debug, PartialEq)]
pub enum SafetyDecision {
    Allow,
    Deny(String),
}

pub fn require_confirmation_token() -> String {
    let random_str: String = rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(8)
        .map(char::from)
        .collect();
    format!("PHOENIX-CONFIRM-{}", random_str.to_uppercase())
}

pub fn is_valid_token(token: &str) -> bool {
    token.starts_with("PHOENIX-CONFIRM-") && token.len() == 24
}

pub fn can_write_to_disk(ctx: &SafetyContext, is_system_disk: bool) -> SafetyDecision {
    if is_system_disk && !ctx.force_mode {
        return SafetyDecision::Deny("CRITICAL: Destructive operations on system disks are BLOCKED. Use force_mode=true to override.".to_string());
    }

    match &ctx.confirmation_token {
        Some(token) if is_valid_token(token) => SafetyDecision::Allow,
        Some(_) => SafetyDecision::Deny("Invalid confirmation token format.".to_string()),
        None => SafetyDecision::Deny(
            "Confirmation token required for destructive operations.".to_string(),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_generation() {
        let token = require_confirmation_token();
        assert!(is_valid_token(&token));
    }

    #[test]
    fn test_safety_policy() {
        let ctx_none = SafetyContext {
            force_mode: false,
            confirmation_token: None,
        };
        assert!(matches!(
            can_write_to_disk(&ctx_none, false),
            SafetyDecision::Deny(_)
        ));

        let token = require_confirmation_token();
        let ctx_valid = SafetyContext {
            force_mode: false,
            confirmation_token: Some(token),
        };
        assert_eq!(can_write_to_disk(&ctx_valid, false), SafetyDecision::Allow);

        // System disk block
        assert!(matches!(
            can_write_to_disk(&ctx_valid, true),
            SafetyDecision::Deny(_)
        ));

        let ctx_force = SafetyContext {
            force_mode: true,
            confirmation_token: ctx_valid.confirmation_token,
        };
        assert_eq!(can_write_to_disk(&ctx_force, true), SafetyDecision::Allow);
    }
}

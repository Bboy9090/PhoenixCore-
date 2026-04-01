use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct SafetyContext {
    pub force_mode: bool,
    pub confirmation_token: Option<String>,
}

#[derive(Debug, Clone)]
pub enum SafetyDecision {
    Allow,
    Deny(String),
}

pub fn require_confirmation_token() -> String {
    format!("PHX-{}", Uuid::new_v4())
}

pub fn can_write_to_disk(ctx: &SafetyContext, is_system_disk: bool) -> SafetyDecision {
    if !ctx.force_mode {
        return SafetyDecision::Deny("Denied: destructive ops require force-mode".to_string());
    }

    let Some(token) = &ctx.confirmation_token else {
        return SafetyDecision::Deny("Denied: confirmation token missing".to_string());
    };
    if !token.starts_with("PHX-") {
        return SafetyDecision::Deny("Denied: invalid confirmation token".to_string());
    }

    if is_system_disk {
        return SafetyDecision::Allow;
    }

    SafetyDecision::Allow
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn denies_without_force() {
        let ctx = SafetyContext {
            force_mode: false,
            confirmation_token: None,
        };
        assert!(matches!(
            can_write_to_disk(&ctx, false),
            SafetyDecision::Deny(_)
        ));
    }

    #[test]
    fn denies_without_token() {
        let ctx = SafetyContext {
            force_mode: true,
            confirmation_token: None,
        };
        assert!(matches!(
            can_write_to_disk(&ctx, false),
            SafetyDecision::Deny(_)
        ));
    }

    #[test]
    fn denies_invalid_token() {
        let ctx = SafetyContext {
            force_mode: true,
            confirmation_token: Some("BAD".to_string()),
        };
        assert!(matches!(
            can_write_to_disk(&ctx, false),
            SafetyDecision::Deny(_)
        ));
    }

    #[test]
    fn allows_with_token() {
        let ctx = SafetyContext {
            force_mode: true,
            confirmation_token: Some("PHX-123".to_string()),
        };
        assert!(matches!(
            can_write_to_disk(&ctx, false),
            SafetyDecision::Allow
        ));
    }
}

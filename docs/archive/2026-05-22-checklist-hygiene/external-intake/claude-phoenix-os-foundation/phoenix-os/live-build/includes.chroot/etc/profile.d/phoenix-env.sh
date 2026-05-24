#!/bin/sh
# Phoenix OS — Shell Environment Profile
# File: /etc/profile.d/phoenix-env.sh
#
# Sets environment variables and shell aliases for all Phoenix OS sessions.
# Sourced by /etc/profile for login shells.

# ---- Phoenix version info ----
export PHOENIX_OS_VERSION="0.1.0-alpha"
export PHOENIX_OS_CODENAME="Ember"

# ---- Disk audit log path (used by tools and wrappers) ----
export PHOENIX_DISK_LOG="/var/log/phoenix/disk-ops.log"

# ---- PATH additions ----
export PATH="/usr/local/bin:${PATH}"

# ---- Aliases: safety-first disk ops ----
# These aliases wrap dangerous commands with a warning.
# Production tools (Phoenix Recovery) implement proper confirmation gates.
alias dd='echo "[Phoenix] Use Phoenix Recovery for disk imaging. Raw dd is available as: command dd"; false'

# Restore raw dd when explicitly needed (escape hatch)
alias rawdd='command dd'

# ---- Aliases: convenience ----
alias lsblk='lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,FSTYPE,MOUNTPOINT,LABEL'
alias df='df -h'
alias free='free -h'

# ---- PHOENIX MOTD function ----
phoenix_motd() {
    printf "\n"
    printf "  \033[38;2;245;140;31m██████  \033[0m Phoenix OS %s\n" "${PHOENIX_OS_VERSION}"
    printf "  \033[38;2;232;100;26m██████  \033[0m Repair-First · Creator-Ready · Recovery-Proven\n"
    printf "  \033[38;2;217;66;21m██████  \033[0m\n"
    printf "\n"
    printf "  Disk audit log : %s\n" "${PHOENIX_DISK_LOG}"
    printf "  Control Center : phoenix-control-center\n"
    printf "  Recovery       : phoenix-recovery\n"
    printf "  System report  : phoenix-sysinfo\n"
    printf "\n"
}

# Show MOTD only in interactive shells
case "$-" in
    *i*) phoenix_motd ;;
esac

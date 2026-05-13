#!/usr/bin/env python3
# Phoenix OS — Calamares: phoenix-postinstall module
# File: installer/calamares-config/modules/phoenix-postinstall.py
#
# Custom Calamares Python module that performs Phoenix OS-specific
# post-installation setup inside the target chroot.
#
# Runs after unpackfs and before the display manager and bootloader steps.
#
# This module:
#   1. Removes the live-user (phoenix) from the installed system
#   2. Configures the Phoenix audit log directory
#   3. Writes the GRUB theme path to /etc/default/grub
#   4. Sets the installed system hostname to what the user chose
#   5. Marks the installation as non-live (removes live-session flags)

import os
import subprocess
import libcalamares


def pretty_name():
    return "Configuring Phoenix OS…"


def run():
    """
    Main entry point called by Calamares.
    Returns None on success, or a (short, long) tuple on error.
    """
    root_mount = libcalamares.globalstorage.value("rootMountPoint")
    if not root_mount:
        return ("No root mount point", "rootMountPoint is not set in global storage.")

    hostname = libcalamares.globalstorage.value("hostname") or "phoenix"

    jobs = [
        ("Removing live user",           lambda: remove_live_user(root_mount)),
        ("Creating log directory",        lambda: create_log_dir(root_mount)),
        ("Configuring GRUB theme",        lambda: configure_grub(root_mount)),
        ("Setting hostname",              lambda: set_hostname(root_mount, hostname)),
        ("Removing live-session markers", lambda: remove_live_markers(root_mount)),
        ("Updating initramfs",            lambda: update_initramfs(root_mount)),
    ]

    total = len(jobs)
    for i, (label, fn) in enumerate(jobs):
        libcalamares.job.setprogress((i + 1) / total)
        libcalamares.utils.debug(f"phoenix-postinstall: {label}")
        try:
            fn()
        except Exception as e:
            libcalamares.utils.warning(f"phoenix-postinstall: {label} failed: {e}")
            # Non-fatal — continue with other steps

    return None


# ---- Step implementations ----

def remove_live_user(root):
    """Remove the 'phoenix' live user from the installed system."""
    chroot(root, ["userdel", "-r", "phoenix"])


def create_log_dir(root):
    """Create Phoenix audit log directory with correct permissions."""
    log_dir = os.path.join(root, "var", "log", "phoenix")
    os.makedirs(log_dir, exist_ok=True)
    # Readable by root and phoenix group only
    os.chmod(log_dir, 0o750)


def configure_grub(root):
    """Write Phoenix GRUB theme and boot parameters to /etc/default/grub."""
    grub_default = os.path.join(root, "etc", "default", "grub")

    if not os.path.exists(grub_default):
        return

    with open(grub_default, "r") as f:
        content = f.read()

    replacements = {
        'GRUB_TIMEOUT=':           'GRUB_TIMEOUT=5',
        'GRUB_DISTRIBUTOR=':       'GRUB_DISTRIBUTOR="Phoenix OS"',
        'GRUB_CMDLINE_LINUX_DEFAULT=': 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3"',
    }

    for key, value in replacements.items():
        lines = content.splitlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith(key):
                new_lines.append(value)
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(value)
        content = "\n".join(new_lines)

    # Add GRUB theme if not already set
    if "GRUB_THEME=" not in content:
        content += '\nGRUB_THEME="/boot/grub/themes/phoenix/theme.txt"\n'

    with open(grub_default, "w") as f:
        f.write(content)


def set_hostname(root, hostname):
    """Write the chosen hostname to /etc/hostname and /etc/hosts."""
    hostname_file = os.path.join(root, "etc", "hostname")
    with open(hostname_file, "w") as f:
        f.write(hostname.strip() + "\n")

    hosts_file = os.path.join(root, "etc", "hosts")
    hosts_content = (
        "127.0.0.1   localhost\n"
        f"127.0.1.1   {hostname}\n"
        "::1         localhost ip6-localhost ip6-loopback\n"
        "ff02::1     ip6-allnodes\n"
        "ff02::2     ip6-allrouters\n"
    )
    with open(hosts_file, "w") as f:
        f.write(hosts_content)


def remove_live_markers(root):
    """Remove files that mark this as a live session."""
    markers = [
        "etc/casper.conf",
        "etc/live/config.conf",
        "etc/sudoers.d/phoenix-live",  # Live passwordless sudo — NOT for installed system
    ]
    for marker in markers:
        path = os.path.join(root, marker)
        if os.path.exists(path):
            os.remove(path)
            libcalamares.utils.debug(f"  Removed live marker: {path}")


def update_initramfs(root):
    """Regenerate initramfs in the installed chroot."""
    chroot(root, ["update-initramfs", "-u", "-k", "all"])


# ---- Chroot helper ----

def chroot(root, cmd):
    """Run a command inside the target chroot."""
    full_cmd = ["chroot", root] + cmd
    result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        libcalamares.utils.warning(
            f"chroot command failed: {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result

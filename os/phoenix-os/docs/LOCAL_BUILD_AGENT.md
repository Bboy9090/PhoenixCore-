# Phoenix OS Local Build Agent

This guide defines safe, non-destructive local setup paths for the Phoenix OS OCI builder.

Scope constraints for PR21:

- No fake ISO success claims
- No host-destructive operations
- No privileged host device passthrough beyond OCI build requirements
- No installer/package-manager replacement logic
- Setup and verification only

## Common Verification Commands

Run these from the repository root after runtime setup:

```bash
bash os/phoenix-os/scripts/check-build-agent.sh
```

```powershell
.\os\phoenix-os\scripts\check-build-agent.ps1
```

If PR20 helper scripts are present, local container checks/builds are:

```bash
bash os/phoenix-os/scripts/verify-container.sh
bash os/phoenix-os/scripts/build-container.sh
```

## 1) Windows 11 + WSL2 + Docker Desktop

### A. Enable WSL2 and install Ubuntu

Run in elevated PowerShell:

```powershell
wsl --install
wsl --set-default-version 2
wsl --install -d Ubuntu
```

Reboot if prompted.

### B. Install and configure Docker Desktop

1. Install Docker Desktop for Windows.
2. In Docker Desktop Settings:
- `General` -> enable `Use the WSL 2 based engine`
- `Resources` -> `WSL Integration` -> enable integration for `Ubuntu`

### C. Verify from PowerShell

```powershell
docker version
docker compose version
.\os\phoenix-os\scripts\check-build-agent.ps1 -Distro Ubuntu -CheckWSLDocker
```

### D. Verify from Ubuntu (inside WSL)

```bash
docker version
docker compose version
bash os/phoenix-os/scripts/check-build-agent.sh
```

### E. Recommended repo location

Use the repository inside the WSL filesystem, not on `/mnt/c`:

```bash
mkdir -p ~/src
cd ~/src
git clone https://github.com/bboy9090/phoenixcore-.git
cd phoenixcore-
```

Recommended WSL path:

```text
/home/<your-user>/src/phoenixcore-
```

### F. Common failure modes

- `docker` works in PowerShell but fails inside Ubuntu: WSL integration is disabled in Docker Desktop.
- `docker: command not found` in PowerShell: Docker Desktop install incomplete or terminal needs restart.
- `Cannot connect to the Docker daemon`: Docker Desktop service is not running.
- `WSL 1` distro version: run `wsl --set-version Ubuntu 2`.
- Build files on `/mnt/c` are slow and may produce permission/line-ending issues.
- BIOS/UEFI virtualization disabled.

## 2) Native Linux

### A. Install Docker or Podman

Use your distro's official install docs. Example for Ubuntu/Debian with Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
```

Example for Podman:

```bash
sudo apt-get update
sudo apt-get install -y podman
```

### B. Verify runtime and privileged container support

```bash
bash os/phoenix-os/scripts/check-build-agent.sh
bash os/phoenix-os/scripts/check-build-agent.sh --check-privileged
```

### C. Run Phoenix OS container checks/builds

If available from PR20:

```bash
bash os/phoenix-os/scripts/verify-container.sh
bash os/phoenix-os/scripts/build-container.sh
```

## 3) macOS (Docker Desktop)

### A. Install Docker Desktop

Install Docker Desktop for macOS and launch it once.

### B. Verify Docker and Compose

```bash
docker version
docker compose version
bash os/phoenix-os/scripts/check-build-agent.sh
```

### C. Run container verification

```bash
bash os/phoenix-os/scripts/check-build-agent.sh --check-privileged
```

If available from PR20:

```bash
bash os/phoenix-os/scripts/verify-container.sh
```

### D. Current macOS limitations

- Linux container builds run inside Docker Desktop's VM, not directly on Darwin.
- `--privileged` behavior is mediated by Docker Desktop's Linux VM.
- Large image builds are sensitive to Docker Desktop memory/disk allocation.
- Host block-device passthrough is intentionally out of scope for this OCI build path.

## Truth Boundary

Successful preflight checks only confirm build-agent readiness.

ISO generation can only be claimed after a real build command completes successfully on an active Docker/Podman runtime.

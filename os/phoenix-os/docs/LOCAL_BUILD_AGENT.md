# Local Build Agent Setup: Phoenix OS

This guide provides step-by-step instructions for configuring a local build agent to generate Phoenix OS ISO artifacts using the OCI build environment.

## 1. Windows 11 + WSL2 + Docker Desktop (Recommended)

### Prerequisites
- **WSL2 Enabled**: Run `wsl --install` in an elevated PowerShell.
- **Linux Distribution**: Install Ubuntu from the Microsoft Store.
- **Docker Desktop**: [Download and install](https://www.docker.com/products/docker-desktop/).

### Configuration
1. Open Docker Desktop Settings.
2. Navigate to **General** and ensure "Use the WSL 2 based engine" is checked.
3. Navigate to **Resources > WSL Integration**.
4. Enable integration for your installed Ubuntu distribution.

### Verification
Run the following from PowerShell:
```powershell
./os/phoenix-os/scripts/check-build-agent.ps1
```

### Performance Tip
For maximum build performance, clone the repository directly into the WSL filesystem (e.g., `\\wsl$\Ubuntu\home\user\phoenix-core-enterprise`) instead of using the Windows `/mnt/c/` drive.

---

## 2. Native Linux (Debian/Ubuntu/Fedora)

### Prerequisites
- **Docker** or **Podman** installed.
- **Privileged Mode Support**: Required for loopback mounts.

### Setup
```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-compose-plugin
sudo usermod -aG docker $USER
```

### Verification
```bash
bash os/phoenix-os/scripts/check-build-agent.sh
```

---

## 3. macOS (Intel / Apple Silicon)

### Prerequisites
- **Docker Desktop** installed.

### Setup
1. [Download Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/).
2. Ensure Docker is running in the menu bar.

### Verification
```bash
bash os/phoenix-os/scripts/check-build-agent.sh
```

---

## Common Failure Modes
- **"Privileged mode denied"**: Ensure your container engine allows privileged containers (standard in Docker Desktop).
- **"No space left on device"**: ISO builds require ~20GB of free space in the Docker virtual disk.
- **"Mount failure"**: Ensure you are using the WSL2 backend on Windows; Hyper-V backend has limited support for nested mounts.

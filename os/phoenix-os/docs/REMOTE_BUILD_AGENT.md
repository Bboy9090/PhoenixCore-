# Phoenix OS Remote Build Agent

This guide describes a remote Linux VM path for OCI builds when a local host cannot run Docker/Podman reliably.

## Baseline Recommendation

Use an Ubuntu or Debian VM dedicated to build jobs.

Minimum baseline:

- CPU: 4 vCPU
- RAM: 8 GB (16 GB preferred)
- Disk: 120 GB free for source, layer cache, and build artifacts
- Network: stable outbound access for base image pulls

## Runtime Setup (Docker or Podman)

Example Docker setup on Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
```

Example Podman setup:

```bash
sudo apt-get update
sudo apt-get install -y podman
```

Validate runtime:

```bash
docker version || podman version
```

## Repository Setup

```bash
mkdir -p ~/src
cd ~/src
git clone https://github.com/bboy9090/phoenixcore-.git
cd phoenixcore-
```

Run build-agent checks:

```bash
bash os/phoenix-os/scripts/check-build-agent.sh
bash os/phoenix-os/scripts/check-build-agent.sh --check-privileged
```

## OCI Build Workflow Over SSH

From local machine:

```bash
ssh <user>@<vm-hostname-or-ip>
cd ~/src/phoenixcore-
bash os/phoenix-os/scripts/check-build-agent.sh
bash os/phoenix-os/container/verify-container.sh
bash os/phoenix-os/container/build-container.sh
```

Notes:

- `verify-container.sh` and `build-container.sh` must exist under `os/phoenix-os/container/`.
- Do not claim ISO output unless `build-container.sh` actually completes successfully.

## Artifact Retrieval Path

Recommended remote artifact path:

```text
~/src/phoenixcore-/os/phoenix-os/out/
```

Retrieve artifacts to local machine:

```bash
scp <user>@<vm-hostname-or-ip>:~/src/phoenixcore-/os/phoenix-os/out/* ./
```

For larger outputs, prefer `rsync`:

```bash
rsync -avh <user>@<vm-hostname-or-ip>:~/src/phoenixcore-/os/phoenix-os/out/ ./out/
```

## Operational Guardrails

- Keep VM usage non-destructive and build-only.
- Do not grant extra host device passthrough beyond documented OCI build requirements.
- Use preflight checks before each build window after runtime updates.

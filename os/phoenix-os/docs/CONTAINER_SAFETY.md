# Phoenix OS Container Safety Doctrine

## Principles
The Phoenix OS OCI build environment is designed to be **isolated, auditable, and non-destructive**. While it requires elevated privileges to generate operating system images, these privileges are strictly scoped to the build process.

## 1. Privileged Mode Rationale
The container requires `privileged: true` for the following specific reasons:
- **Loopback Mounting**: `live-build` uses `mount -o loop` to create and manage the target ISO filesystem layers.
- **Chrooting**: The build process executes commands inside a isolated rootfs (chroot), which requires special kernel capabilities.
- **Device Management**: Tools like `mksquashfs` and `xorriso` may require low-level access to block devices or virtual device nodes.

## 2. Isolation Boundaries
- **Volume Mounts**: Only the project root directory is mounted into the container at `/workspace`. The container has no access to host system directories like `/etc`, `/usr`, or user home folders outside the workspace.
- **Network**: The container uses standard bridged networking to fetch packages from Debian/Ubuntu mirrors. No incoming ports are exposed.
- **Persistence**: All build artifacts are written to `os/phoenix-os/build/` and `os/phoenix-os/config/`, ensuring they are persisted on the host for auditing.

## 3. Host Protection
- **No Direct Disk Access**: The container does not mount host physical disks or partitions.
- **No Kernel Modification**: The build process uses the host's kernel but does not attempt to modify it or load custom modules.
- **Non-Destructive Builder**: The `phoenix-builder` user has no permission to execute commands on the host system.

## 4. Audit Checklist
Before running a build, verify:
1. `docker-compose.yml` mounts only the expected workspace path.
2. `Dockerfile` contains only trusted packages from official repositories.
3. `build-iso.sh` contains no commands targeting host paths (e.g., `/dev/sda`, `C:\`).

## 5. Security Recommendations
- **Build in Isolation**: Run ISO builds on dedicated build agents or ephemeral VMs where possible.
- **Scan Artifacts**: Always verify the checksums and contents of the generated `.iso` before deployment.
- **Monitor Build Logs**: Review the output of `build-container.sh` for unexpected network or filesystem activity.

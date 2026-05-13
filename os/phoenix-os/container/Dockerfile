# Phoenix OS OCI Build Environment
# Foundation: Debian Bookworm (Stable)

FROM debian:bookworm-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install core build toolchain for live-build
RUN apt-get update && apt-get install -y --no-install-recommends \
    live-build \
    squashfs-tools \
    xorriso \
    debootstrap \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    dosfstools \
    rsync \
    sudo \
    git \
    bash \
    coreutils \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up build user
RUN useradd -m -s /bin/bash phoenix-builder && \
    echo "phoenix-builder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /workspace

# Set ownership
RUN chown phoenix-builder:phoenix-builder /workspace

USER phoenix-builder

# Set default entrypoint
ENTRYPOINT ["/bin/bash"]

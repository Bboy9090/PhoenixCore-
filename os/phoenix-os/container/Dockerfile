# Phoenix OS OCI builder.
#
# This image contains live-build tooling only. Host orchestration stays in the
# wrapper scripts so the container cannot format disks or discover host devices.
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      coreutils \
      cpio \
      curl \
      debootstrap \
      dosfstools \
      file \
      findutils \
      git \
      grep \
      grub-common \
      isolinux \
      live-build \
      mtools \
      python3 \
      rsync \
      sed \
      squashfs-tools \
      sudo \
      syslinux-common \
      tar \
      xorriso \
      xz-utils; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) \
        apt-get install -y --no-install-recommends grub-pc-bin; \
        efi_pkg="grub-efi-amd64-bin grub-efi-ia32-bin" \
        ;; \
      arm64) efi_pkg="grub-efi-arm64-bin" ;; \
      *) echo "Unsupported architecture for EFI GRUB package: $arch"; exit 1 ;; \
    esac; \
    apt-get install -y --no-install-recommends $efi_pkg; \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash phoenix-builder \
    && echo "phoenix-builder ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/phoenix-builder \
    && chmod 0440 /etc/sudoers.d/phoenix-builder

WORKDIR /workspace/os/phoenix-os

CMD ["bash"]

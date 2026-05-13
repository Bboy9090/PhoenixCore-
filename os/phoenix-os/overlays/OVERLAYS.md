# Phoenix OS Overlays

Place files in this directory to be overlaid onto the target filesystem during the live-build process.

## Example Structure
`overlays/etc/systemd/system/phoenix-agent.service`
`overlays/etc/sddm.conf.d/phoenix.conf`
`overlays/usr/share/wallpapers/phoenix/`

## Usage
The `build-iso.sh` script will copy these files into the chroot environment before the final squashfs generation.

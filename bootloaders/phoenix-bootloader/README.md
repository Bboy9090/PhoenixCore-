# Phoenix Bootloader Package

Put your custom bootloader binaries here. The staging workflow expects:

```
EFI/BOOT/BOOTX64.EFI
```

Optional:
- EFI/BOOT/BOOTAA64.EFI
- EFI/BOOT/BOOTIA32.EFI

Stage onto a target mount:
```
phoenix-cli stage-bootloader \
  --source bootloaders/phoenix-bootloader \
  --target-mount /Volumes/USB \
  --execute --force --token PHX-...
```

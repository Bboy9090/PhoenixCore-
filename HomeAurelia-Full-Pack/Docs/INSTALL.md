# 💿 Technical Installation Sheet

## Staging Requirements
* Target OS: Debian Live Build / KDE Plasma Desktop Environment.
* Sound Server: PipeWire or PulseAudio (for ambient chimes).
* Window Manager: KWin with Aurorae support.

## Execution
Run the core installation script directly from the root of the theme pack:
```bash
chmod +x Scripts/*.sh
./Scripts/install.sh
```

## Selecting an Edition
To instantly re-render the dynamic desktop parameters, execute the apply script:
```bash
./Scripts/apply-aurelia.sh
# or apply-arcwyre.sh, apply-thundergod.sh, apply-native.sh
```

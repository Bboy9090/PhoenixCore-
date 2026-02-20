# OpenCore Legacy Patcher Integration

BootForge embeds [OpenCore Legacy Patcher (OCLP)](https://github.com/dortania/OpenCore-Legacy-Patcher) to boot unsupported Macs on newer macOS versions.

## Setup

1. **Initialize the OCLP submodule:**
   ```
   git submodule update --init third_party/OpenCore-Legacy-Patcher
   ```

2. **Install OCLP dependencies (macOS only):**
   ```
   pip install wxpython pyobjc
   ```

## Usage

- **From BootForge:** Tools → OpenCore Legacy Patcher
- Launches the full OCLP GUI in a separate window
- OCLP is macOS-only; on other platforms the menu shows an explanatory message

## What's Included

- **Full OCLP:** GUI, build, install, root patching
- **No download at runtime:** OCLP is vendored via git submodule
- **Single entry point:** BootForge provides one-click access

## License

OCLP is licensed under the BSD 2-Clause License. See `third_party/OpenCore-Legacy-Patcher/LICENSE` for details.

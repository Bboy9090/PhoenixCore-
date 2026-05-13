# Contributing to Phoenix OS

Thank you for your interest in contributing to Phoenix OS! This document provides guidelines for participating in the project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our Code of Conduct in all interactions.

## Ways to Contribute

### Reporting Bugs

If you find a bug, please report it by opening an issue on GitHub. Include:

- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, hardware, etc.)
- Relevant logs or error messages

### Suggesting Features

We welcome feature suggestions! Please open an issue with:

- Clear description of the feature
- Use cases and benefits
- Possible implementation approach
- Any relevant mockups or examples

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages: `git commit -m "Add feature: description"`
6. Push to your fork
7. Open a Pull Request with detailed description

### Improving Documentation

Documentation improvements are always welcome! You can:

- Fix typos and clarify existing documentation
- Add new guides and tutorials
- Improve code comments
- Add examples

### Testing

Help us test Phoenix OS by:

- Testing new features and reporting issues
- Testing on different hardware
- Testing different installation scenarios
- Performance testing and optimization

### Translations

Help translate Phoenix OS to other languages:

- Translate UI strings
- Translate documentation
- Translate error messages

## Development Setup

### Prerequisites

- Ubuntu 22.04 LTS or Debian 12
- 50GB free disk space
- 4GB RAM minimum
- Internet connection

### Building Phoenix OS

```bash
# Clone the repository
git clone https://github.com/Bboy9090/phoenix-os.git
cd phoenix-os

# Verify your system
./scripts/verify-host.sh

# Build the ISO
./scripts/build-iso.sh
```

### Testing Changes

```bash
# Test in QEMU
qemu-system-x86_64 -m 2048 -cdrom dist/phoenix-os-2.0.0-amd64.iso

# Write to USB for testing on real hardware
sudo dd if=dist/phoenix-os-2.0.0-amd64.iso of=/dev/sdX bs=4M status=progress
```

## Coding Standards

### Shell Scripts

- Use `#!/bin/bash` shebang
- Use `set -e` for error handling
- Quote variables: `"$VAR"` not `$VAR`
- Use meaningful variable names
- Add comments for complex logic
- Test on both Bash 4 and 5

### Documentation

- Use Markdown format
- Keep lines under 80 characters where possible
- Use clear, concise language
- Include code examples
- Add table of contents for long documents

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Limit first line to 50 characters
- Reference issues: "Fixes #123"
- Explain what and why, not how

Example:
```
Add disk safety validation for USB devices

Implement 5-layer validation system to prevent accidental
data loss on internal disks. Validates device identification,
partition integrity, data loss risk, bootloader compatibility,
and post-build verification.

Fixes #42
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers
6. Address review feedback
7. Squash commits if requested
8. Merge when approved

## Issue Labels

- `bug` — Something isn't working
- `enhancement` — New feature or improvement
- `documentation` — Documentation improvements
- `good first issue` — Good for newcomers
- `help wanted` — Extra attention needed
- `question` — Further information requested
- `wontfix` — This will not be worked on

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR — Breaking changes
- MINOR — New features (backward compatible)
- PATCH — Bug fixes

See RELEASE_CHECKLIST.md for detailed release procedures.

## Getting Help

- **Issues:** https://github.com/Bboy9090/phoenix-os/issues
- **Discussions:** https://github.com/Bboy9090/phoenix-os/discussions
- **Documentation:** https://github.com/Bboy9090/phoenix-os/tree/main/docs

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page
- Project documentation

Thank you for contributing to Phoenix OS!

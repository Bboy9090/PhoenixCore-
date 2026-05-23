# Command Control Center - Production Release Checklist

This checklist ensures that Command (PhoenixCore UI) meets Bobby's Worldwide OS production standards before release.

## Pre-Release Validation

### Code Quality

- [ ] All linters pass without errors
  - [ ] `cargo clippy -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32`
  - [ ] `cargo fmt --check`
  - [ ] Frontend ESLint checks (if applicable)

- [ ] All tests pass on all platforms
  - [ ] `cargo test -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 -p phoenix-bootloader-core -p phoenix-wim`
  - [ ] `python -m pytest tests/`
  - [ ] Frontend tests (if applicable)

- [ ] No compiler warnings in release builds
  - [ ] `cargo build --release -p phoenix-core`
  - [ ] `pnpm run build` (Control Center)

### Build Verification

- [ ] Clean build from scratch succeeds
  - [ ] `cargo clean && cargo build --workspace` (compilable crates)
  - [ ] `rm -rf node_modules && pnpm install && pnpm run build`
  - [ ] `pip install -r requirements.txt && python -m pytest tests/`

- [ ] Smoke tests pass on all entry points
  - [ ] `./scripts/smoke-test.sh` completes successfully
  - [ ] All CLI commands execute without errors
  - [ ] GUI launches and displays correctly
  - [ ] Backend server starts and responds to health checks

- [ ] Health check validates system state
  - [ ] `./scripts/healthcheck.sh` passes all checks
  - [ ] Edition manifest loads correctly
  - [ ] App registry is accessible
  - [ ] Core services are healthy

### Platform Support

- [ ] **Linux** build and tests pass
  - [ ] Ubuntu 20.04+
  - [ ] Debian 11+
  - [ ] Fedora 36+

- [ ] **macOS** build and tests pass
  - [ ] macOS 11 Big Sur+
  - [ ] Intel and Apple Silicon

- [ ] **Windows** build and tests pass
  - [ ] Windows 10 21H2+
  - [ ] Windows 11

### Documentation

- [ ] README.md is up-to-date
  - [ ] Build instructions are accurate
  - [ ] Test instructions are accurate
  - [ ] Package instructions are accurate
  - [ ] All links work

- [ ] PRD.md reflects current features
  - [ ] Feature list is accurate
  - [ ] MVP scope is defined
  - [ ] Out-of-scope items are listed

- [ ] APP_CONTRACT.md is complete
  - [ ] Launcher integration is documented
  - [ ] API contracts are defined
  - [ ] Data formats are specified

- [ ] API documentation is current
  - [ ] All endpoints documented
  - [ ] Request/response schemas defined
  - [ ] Error codes documented

### Edition Support

- [ ] ARCWYRE Edition loads correctly
  - [ ] Theme colors apply
  - [ ] Branding displays
  - [ ] Safety rules enforce

- [ ] Thunder God Edition loads correctly
  - [ ] Theme colors apply
  - [ ] Branding displays
  - [ ] Safety rules enforce

- [ ] Forge Edition loads correctly
  - [ ] Theme colors apply
  - [ ] Branding displays
  - [ ] Safety rules enforce

- [ ] Blue Phoenix Edition loads correctly
  - [ ] Theme colors apply
  - [ ] Branding displays
  - [ ] Safety rules enforce

### Feature Validation

- [ ] System Overview Panel
  - [ ] CPU info displays accurately
  - [ ] Memory usage is correct
  - [ ] Disk usage shows all volumes
  - [ ] Network interfaces listed
  - [ ] OS/kernel version correct
  - [ ] Updates in real-time

- [ ] App Readiness Panel
  - [ ] Reads app metadata correctly
  - [ ] Displays app versions
  - [ ] Shows health status
  - [ ] Launcher integration works

- [ ] Service Status Panel
  - [ ] Backend health check works
  - [ ] Rust core status accurate
  - [ ] Safety gates show correct state
  - [ ] Service indicators update

- [ ] Edition Identity Panel
  - [ ] Edition name displays
  - [ ] Theme loads correctly
  - [ ] Features list is accurate
  - [ ] Safety policy summary correct

### Security & Safety

- [ ] No hardcoded secrets or credentials
- [ ] API endpoints require authentication (if production)
- [ ] Input validation on all user inputs
- [ ] Safety gates prevent destructive operations
- [ ] Dry-run mode available for recovery ops
- [ ] Audit logging for sensitive operations
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No command injection vulnerabilities

### Performance

- [ ] Dashboard loads in < 2 seconds
- [ ] API responses in < 500ms
- [ ] Memory usage < 100MB (idle)
- [ ] CPU usage < 5% (idle)
- [ ] No memory leaks after 1 hour
- [ ] Responsive UI (60fps animations)

### Packaging

- [ ] Windows MSIX package builds
  - [ ] Package manifest is valid
  - [ ] Install/uninstall works
  - [ ] Start menu integration
  - [ ] See `packaging/README.md`

- [ ] macOS .app bundle builds (if applicable)
  - [ ] Code signing (if applicable)
  - [ ] Notarization (if applicable)

- [ ] Linux packages build (if applicable)
  - [ ] .deb package
  - [ ] .rpm package
  - [ ] AppImage (if applicable)

### Deployment

- [ ] Version number updated
  - [ ] `Cargo.toml` versions
  - [ ] `package.json` versions
  - [ ] `app.metadata.json` version

- [ ] CHANGELOG.md updated
  - [ ] New features listed
  - [ ] Bug fixes listed
  - [ ] Breaking changes noted

- [ ] Git tags created
  - [ ] Tag format: `v1.0.0`
  - [ ] Signed tags (if applicable)

- [ ] Release notes prepared
  - [ ] Feature highlights
  - [ ] Known issues
  - [ ] Upgrade instructions

### Post-Release Validation

- [ ] Installation tested on clean system
- [ ] Upgrade path tested (if applicable)
- [ ] Rollback tested (if applicable)
- [ ] Monitoring alerts configured (if production)
- [ ] Support documentation published
- [ ] User feedback channels ready

## Sign-Off

- [ ] **Engineering Lead**: Code review complete
- [ ] **QA Lead**: Testing complete
- [ ] **Product Owner**: Features approved
- [ ] **Security Review**: Security scan passed
- [ ] **Release Manager**: Ready for release

## Release Notes Template

```markdown
# Command Control Center v1.0.0

## New Features
- System Overview Panel with real-time metrics
- App Readiness Panel with metadata integration
- Service Status Panel for core health monitoring
- Edition Identity Panel supporting all BWOS editions

## Improvements
- Enhanced build process with clear instructions
- Comprehensive test coverage
- Production-grade documentation

## Bug Fixes
- N/A (initial release)

## Known Issues
- Historical metrics not yet implemented (planned for v1.1)
- Remote monitoring not available (planned for v1.2)

## Upgrade Instructions
- First release, no upgrade path

## Platform Support
- Linux: Ubuntu 20.04+, Debian 11+, Fedora 36+
- macOS: macOS 11+, Intel and Apple Silicon
- Windows: Windows 10 21H2+, Windows 11
```

## Automated Checks

Run these commands to automate validation:

```bash
# Run all tests
./scripts/smoke-test.sh

# Run health checks
./scripts/healthcheck.sh

# Build all targets
python build_system/build_all.py

# Lint and format
cargo clippy --all-targets && cargo fmt --check
```

## Emergency Rollback Plan

If critical issues are discovered post-release:

1. Immediately pull release from distribution
2. Communicate issue to users via release notes
3. Tag rollback version: `v1.0.0-rollback`
4. Deploy previous stable version
5. Create hotfix branch for critical fix
6. Follow expedited release process for hotfix

## Support Contacts

- **Engineering**: [Insert contact]
- **QA**: [Insert contact]
- **Product**: [Insert contact]
- **Release Management**: [Insert contact]

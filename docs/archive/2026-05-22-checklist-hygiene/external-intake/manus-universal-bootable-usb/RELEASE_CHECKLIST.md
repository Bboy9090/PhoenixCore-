# Phoenix OS Release Checklist

**Pre-release verification checklist for Phoenix OS ISO releases**

---

## Pre-Release (1 Week Before)

### Code Quality

- [ ] All unit tests passing: `./tests/smoke/run-tests.sh`
- [ ] No critical bugs in issue tracker
- [ ] Code review completed for all changes
- [ ] Security audit completed
- [ ] Performance benchmarks acceptable
- [ ] Documentation updated and reviewed

### Build Verification

- [ ] ISO builds successfully on Ubuntu 22.04 LTS
- [ ] ISO builds successfully on Debian 12
- [ ] Build time acceptable (< 60 minutes)
- [ ] ISO size reasonable (< 3GB)
- [ ] All packages included and verified
- [ ] No build warnings or errors

### Testing

- [ ] Boot test on QEMU (x86_64)
- [ ] Boot test on real hardware (3+ devices)
- [ ] Live system functionality verified
- [ ] Installer (Calamares) tested
- [ ] Post-install system boots correctly
- [ ] Network connectivity works
- [ ] Audio and graphics functional

---

## Release Day (24 Hours Before)

### Final Builds

- [ ] Clean build from scratch: `./scripts/clean.sh && ./scripts/build-iso.sh`
- [ ] Verify ISO integrity: `./tests/iso-validation/validate.sh`
- [ ] Generate checksums: `sha256sum phoenix-os-*.iso > SHA256SUMS`
- [ ] Sign ISO: `./scripts/sign-iso.sh`
- [ ] Create release notes document
- [ ] Tag git commit: `git tag -a v2.0.0 -m "Release 2.0.0"`

### Documentation

- [ ] README.md updated with new version
- [ ] CHANGELOG.md created with release notes
- [ ] Installation guide verified
- [ ] Known issues documented
- [ ] Upgrade path documented (if applicable)
- [ ] Security advisories reviewed

### Artifacts

- [ ] ISO file: `phoenix-os-2.0.0-amd64.iso`
- [ ] Checksum file: `SHA256SUMS`
- [ ] Signature file: `SHA256SUMS.asc`
- [ ] Release notes: `RELEASE_NOTES.md`
- [ ] Installation guide: `INSTALL.md`
- [ ] Known issues: `KNOWN_ISSUES.md`

---

## Release (Day Of)

### GitHub Release

- [ ] Create GitHub release: https://github.com/Bboy9090/phoenix-os/releases/new
- [ ] Upload ISO file
- [ ] Upload checksum file
- [ ] Upload signature file
- [ ] Add release notes
- [ ] Mark as "Latest release"
- [ ] Announce on GitHub discussions

### Distribution

- [ ] Upload to primary mirror
- [ ] Upload to backup mirrors
- [ ] Verify download links work
- [ ] Test download integrity
- [ ] Verify mirror availability
- [ ] Monitor download speeds

### Announcement

- [ ] Post on GitHub discussions
- [ ] Send email to mailing list
- [ ] Post on social media (Twitter, Reddit, etc.)
- [ ] Update website with new version
- [ ] Update documentation links
- [ ] Notify partners and integrations

---

## Post-Release (1 Week After)

### Monitoring

- [ ] Monitor download statistics
- [ ] Track issue reports
- [ ] Monitor user feedback
- [ ] Check for critical bugs
- [ ] Verify no security issues
- [ ] Monitor system stability

### Support

- [ ] Respond to user questions
- [ ] Help troubleshoot issues
- [ ] Document common problems
- [ ] Create FAQ if needed
- [ ] Update documentation based on feedback
- [ ] Plan hotfixes if critical issues found

### Analysis

- [ ] Analyze download statistics
- [ ] Review user feedback
- [ ] Identify improvement areas
- [ ] Plan next release features
- [ ] Update roadmap if needed
- [ ] Create post-release report

---

## Release Candidate (RC) Testing

### For Major Releases (2.0, 3.0, etc.)

**1 Month Before Release**

- [ ] Create release candidate branch: `git checkout -b rc/2.0.0`
- [ ] Build RC ISO: `./scripts/build-iso.sh --rc`
- [ ] Tag RC: `git tag -a v2.0.0-rc1 -m "Release Candidate 1"`
- [ ] Announce RC for community testing
- [ ] Distribute RC ISO to testers

**Testing Phase (2 Weeks)**

- [ ] Collect feedback from testers
- [ ] Fix critical bugs found
- [ ] Create RC2 if major issues found
- [ ] Verify fixes in new RC
- [ ] Get sign-off from testers
- [ ] Finalize release date

**Release Preparation**

- [ ] Merge RC branch to main: `git merge rc/2.0.0`
- [ ] Create final release build
- [ ] Verify all tests pass
- [ ] Generate final artifacts
- [ ] Prepare announcement
- [ ] Schedule release

---

## Version Numbering

Phoenix OS uses semantic versioning: `MAJOR.MINOR.PATCH`

### Version Format

- **MAJOR** (2, 3, 4, etc.) — Major feature releases, significant changes
- **MINOR** (0, 1, 2, etc.) — Feature additions, improvements
- **PATCH** (0, 1, 2, etc.) — Bug fixes, security updates

### Examples

- `2.0.0` — Initial release (MVP)
- `2.1.0` — Enhanced tools and diagnostics
- `2.1.1` — Bug fix for 2.1.0
- `2.2.0` — Custom applications
- `3.0.0` — Major new features

---

## Hotfix Releases

### When to Release a Hotfix

- Critical security vulnerability
- Data loss bug
- System crash or hang
- Installation failure
- Major feature broken

### Hotfix Process

1. Create hotfix branch: `git checkout -b hotfix/2.0.1`
2. Fix the issue and test thoroughly
3. Update version number: `2.0.1`
4. Build hotfix ISO: `./scripts/build-iso.sh`
5. Run full test suite
6. Create GitHub release
7. Announce hotfix immediately
8. Merge back to main

### Hotfix Timeline

- **Discovery to Release:** < 24 hours for critical issues
- **Testing:** Minimum 4 hours
- **Announcement:** Immediate upon release

---

## Security Release Process

### Security Vulnerability Handling

1. **Report** — Receive vulnerability report (security@phoenixos.io)
2. **Verify** — Confirm vulnerability and impact
3. **Fix** — Develop and test fix
4. **Prepare** — Create security release
5. **Coordinate** — Notify stakeholders
6. **Release** — Publish security update
7. **Announce** — Disclose vulnerability details

### Security Release Timeline

- **Critical:** Release within 24 hours
- **High:** Release within 72 hours
- **Medium:** Release within 1 week
- **Low:** Include in next regular release

### Disclosure Policy

- **Embargo Period:** 30 days before public disclosure
- **Notification:** Notify major distributions and partners
- **CVE:** Request CVE number for tracking
- **Credits:** Acknowledge researcher in release notes

---

## Rollback Procedure

### If Critical Issue Found After Release

1. **Assess** — Determine severity and impact
2. **Decide** — Decide whether to rollback or hotfix
3. **Announce** — Notify users immediately
4. **Rollback** — Remove from mirrors if necessary
5. **Prepare** — Prepare hotfix or new RC
6. **Release** — Release fixed version
7. **Document** — Document what happened and lessons learned

### Rollback Checklist

- [ ] Remove ISO from primary mirrors
- [ ] Remove from backup mirrors
- [ ] Update website to previous version
- [ ] Notify users via email
- [ ] Post on GitHub and social media
- [ ] Prepare hotfix or new release
- [ ] Create post-mortem report

---

## Release Sign-Off

### Required Approvals

- [ ] Project Lead approval
- [ ] Security team approval
- [ ] Quality assurance sign-off
- [ ] Documentation review
- [ ] Community feedback (for major releases)

### Sign-Off Template

```
Release: Phoenix OS 2.0.0
Date: May 8, 2026
Status: APPROVED FOR RELEASE

Approvals:
- [ ] Project Lead: _________________ Date: _______
- [ ] Security Team: ________________ Date: _______
- [ ] QA Lead: _____________________ Date: _______
- [ ] Documentation: ________________ Date: _______

Notes:
_________________________________________________
```

---

## Post-Release Maintenance

### Ongoing Support

- **Bug Fixes:** Patch releases as needed
- **Security Updates:** Within 24-72 hours
- **Documentation:** Keep current and accurate
- **Community:** Respond to issues and feedback
- **Monitoring:** Track stability and performance

### End of Life (EOL)

- **Support Period:** 18 months for minor releases
- **LTS Support:** 3 years for major releases
- **EOL Announcement:** 6 months before EOL date
- **Final Update:** Security patches until EOL date
- **Archive:** Keep ISO available for download

### Support Timeline

| Version | Release | EOL | Status |
|---------|---------|-----|--------|
| 2.0.0 | May 2026 | Nov 2027 | Current |
| 2.1.0 | Sep 2026 | Mar 2028 | Supported |
| 2.2.0 | Dec 2026 | Jun 2028 | Supported |
| 3.0.0 | Jun 2027 | Jun 2030 | LTS |

---

## Continuous Integration

### Automated Checks

Every commit triggers:
- [ ] Build test: ISO builds successfully
- [ ] Boot test: ISO boots in QEMU
- [ ] Package test: All packages install
- [ ] Security scan: Check for vulnerabilities
- [ ] Documentation: Verify docs build

### CI/CD Pipeline

```
Commit → Build → Test → Security Scan → Merge
```

### Failure Handling

- **Build Failure:** Block merge, fix required
- **Test Failure:** Block merge, fix required
- **Security Issue:** Block merge, review required
- **Documentation:** Warning only, can merge

---

## Release Communication Template

### Announcement Email

```
Subject: Phoenix OS 2.0.0 Released!

Dear Phoenix OS Community,

We're excited to announce the release of Phoenix OS 2.0.0!

This release includes:
- Live-build ISO generation system
- KDE Plasma 6 desktop environment
- Calamares installer with custom branding
- PhoenixDrive mobile app integration
- Recovery tools and utilities

Download: https://github.com/Bboy9090/phoenix-os/releases/tag/v2.0.0
Installation Guide: https://github.com/Bboy9090/phoenix-os/blob/main/docs/install.md
Known Issues: https://github.com/Bboy9090/phoenix-os/blob/main/KNOWN_ISSUES.md

Thank you for your support!

The Phoenix OS Team
```

### Social Media Post

```
🔥 Phoenix OS 2.0.0 is here!

Repair-first Linux distribution with:
✅ KDE Plasma 6
✅ PhoenixDrive integration
✅ Recovery tools
✅ Custom branding

Download now: [link]
#LinuxOS #PhoenixOS #OpenSource
```

---

## Checklist Template

Copy this template for each release:

```markdown
# Release Checklist: Phoenix OS X.Y.Z

**Release Date:** YYYY-MM-DD
**Release Manager:** Name
**Status:** [ ] In Progress [ ] Complete [ ] Blocked

## Pre-Release
- [ ] Tests passing
- [ ] Security audit complete
- [ ] Documentation updated
- [ ] ISO builds successfully

## Release Day
- [ ] Final build created
- [ ] Checksums generated
- [ ] GitHub release created
- [ ] Announcement posted

## Post-Release
- [ ] Downloads working
- [ ] User feedback monitored
- [ ] Issues tracked
- [ ] Support provided

## Sign-Off
- [ ] Project Lead: ___________
- [ ] Security: ___________
- [ ] QA: ___________
```

---

**Last Updated:** May 8, 2026  
**Next Review:** After 2.0.0 release

Phoenix OS — Professional Release Management

# GitHub Push Instructions

The Phoenix Ecosystem monorepo is ready to be pushed to GitHub. Follow these instructions to complete the deployment.

---

## Prerequisites

- GitHub account with SSH key configured
- Or GitHub Personal Access Token (PAT) for HTTPS authentication
- Git installed locally

---

## Option 1: SSH Authentication (Recommended)

### Setup SSH Key (if not already done)

1. **Generate SSH key:**
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

2. **Add to SSH agent:**
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

3. **Add public key to GitHub:**
   - Copy: `cat ~/.ssh/id_ed25519.pub`
   - Go to GitHub Settings → SSH and GPG keys
   - Click "New SSH key"
   - Paste and save

### Push Repository

```bash
cd /home/ubuntu/phoenixcore

# Remove HTTPS remote if already added
git remote remove origin

# Add SSH remote
git remote add origin git@github.com:Bboy9090/phoenixcore.git

# Push to GitHub
git push -u origin main
git push -u origin --tags
```

---

## Option 2: HTTPS with Personal Access Token

### Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select scopes: `repo`, `workflow`
4. Copy the token

### Push Repository

```bash
cd /home/ubuntu/phoenixcore

# Remove SSH remote if already added
git remote remove origin

# Add HTTPS remote
git remote add origin https://github.com/Bboy9090/phoenixcore.git

# Push to GitHub (will prompt for token)
git push -u origin main
git push -u origin --tags
```

When prompted for password, enter your Personal Access Token.

---

## Option 3: GitHub CLI (Easiest)

### Install GitHub CLI

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt-get install gh

# Windows (Chocolatey)
choco install gh
```

### Authenticate and Push

```bash
# Login to GitHub
gh auth login

# Navigate to repository
cd /home/ubuntu/phoenixcore

# Push to GitHub
git push -u origin main
git push -u origin --tags
```

---

## Verify Push

After pushing, verify the repository on GitHub:

```bash
# Check remote URL
git remote -v

# Check branch status
git status

# Verify tags
git tag -l
```

---

## GitHub Repository Setup

Once pushed, complete these setup steps on GitHub:

### 1. Configure Branch Protection

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - Require pull request reviews before merging
   - Require status checks to pass
   - Require branches to be up to date

### 2. Enable Actions

1. Go to Actions tab
2. Workflows should be automatically detected
3. Enable CI/CD workflows

### 3. Configure Secrets

1. Go to Settings → Secrets and variables → Actions
2. Add these secrets:
   - `CODECOV_TOKEN` — For coverage reporting
   - `SENTRY_AUTH_TOKEN` — For error tracking
   - `DATADOG_API_KEY` — For monitoring

### 4. Set Up Environments

1. Go to Settings → Environments
2. Create `production` environment
3. Add deployment protection rules if needed

### 5. Configure Pages (Optional)

1. Go to Settings → Pages
2. Set source to `gh-pages` branch
3. Enable custom domain if desired

---

## Troubleshooting

### "fatal: Authentication failed"

**Solution:** Use SSH key or Personal Access Token instead of password.

### "remote: Repository not found"

**Solution:** Verify repository URL is correct and you have access.

### "Permission denied (publickey)"

**Solution:** Ensure SSH key is added to GitHub and SSH agent.

### "Updates were rejected"

**Solution:** Pull latest changes first:
```bash
git pull origin main
git push origin main
```

---

## After Push

### Verify CI/CD

1. Go to GitHub Actions tab
2. Verify workflows are running
3. Check build status

### Monitor Deployments

1. Go to Deployments tab
2. View deployment history
3. Check environment status

### Create Release

```bash
# Create annotated tag
git tag -a v2.0.0 -m "Release version 2.0.0"

# Push tag
git push origin v2.0.0

# Or use GitHub CLI
gh release create v2.0.0 --title "Phoenix Ecosystem v2.0.0"
```

---

## Next Steps

After successful push:

1. **Monitor CI/CD:** Ensure all workflows pass
2. **Create Release:** Tag and release v2.0.0
3. **Build Artifacts:** Download builds from Actions
4. **Deploy:** Follow deployment guides for each component
5. **Announce:** Share with community

---

## Support

For issues with GitHub:
- GitHub Docs: https://docs.github.com
- GitHub Support: https://support.github.com
- Phoenix Discord: https://discord.gg/phoenixos

---

**Phoenix Ecosystem — Ready for GitHub** 🔥

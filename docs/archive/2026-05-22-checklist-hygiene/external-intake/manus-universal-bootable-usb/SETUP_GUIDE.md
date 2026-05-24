# Phoenix Control Center - Setup & Development Guide

Complete guide for setting up, developing, and building the Phoenix Control Center application.

## Quick Start

```bash
# Navigate to project
cd /home/ubuntu/phoenix-control-center

# Install dependencies
npm install

# Start development
npm run tauri:dev
```

This will:
1. Start Vite dev server on http://localhost:5173
2. Launch Tauri window with hot reload enabled
3. Enable React DevTools and TypeScript checking

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| RAM | 4GB | 8GB+ |
| Disk | 5GB | 10GB+ |
| Node.js | 18.0.0 | 20.0.0+ |
| npm | 9.0.0 | 9.8.0+ |
| Rust | 1.70.0 | Latest stable |

### Install Node.js & npm

```bash
# Using NodeSource repository (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### Install Rust

```bash
# Download and install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Activate Rust
source $HOME/.cargo/env

# Verify installation
rustc --version
cargo --version
```

### Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  curl \
  wget \
  libssl-dev \
  libxdo-dev \
  libxcb-render0-dev \
  libxcb-shape0-dev \
  libxcb-xfixes0-dev \
  libxkbcommon-dev \
  libssl-dev

# For Tauri development
sudo apt-get install -y \
  libgtk-3-dev \
  libwebkit2gtk-4.0-dev \
  libappindicator3-dev \
  librsvg2-dev \
  patchelf
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/Bboy9090/phoenix-os.git
cd phoenix-os/packages/phoenix-control-center
```

### 2. Install Dependencies

```bash
npm install

# This installs:
# - React 18 and dependencies
# - Tauri CLI and runtime
# - Tailwind CSS and PostCSS
# - TypeScript and development tools
# - Testing frameworks
```

### 3. Verify Installation

```bash
# Check Node.js
node --version

# Check npm
npm --version

# Check Rust
rustc --version

# Check Tauri CLI
npx tauri --version
```

## Development Workflow

### Starting Development Server

```bash
# Option 1: Full Tauri development (recommended)
npm run tauri:dev

# Option 2: Just Vite dev server (for web development)
npm run dev

# Option 3: Just Tauri window (requires separate Vite server)
npm run tauri
```

### Code Quality

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Run tests
npm run test

# Test with UI
npm run test:ui

# Coverage report
npm run test:coverage
```

### Project Structure

```
phoenix-control-center/
├── src/
│   ├── components/          # React components
│   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   └── Header.tsx       # Top header bar
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── SystemInfo.tsx   # System information
│   │   ├── DiskManagement.tsx
│   │   ├── Recovery.tsx
│   │   └── Settings.tsx
│   ├── stores/              # Zustand state management
│   │   ├── themeStore.ts    # Theme (light/dark)
│   │   └── systemStore.ts   # System state
│   ├── services/            # Tauri API services
│   │   └── systemService.ts # System operations
│   ├── types/               # TypeScript types
│   │   └── system.ts        # System types
│   ├── utils/               # Utility functions
│   ├── assets/              # Images and icons
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── index.html               # HTML template
├── tauri.conf.json          # Tauri configuration
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
├── tsconfig.json            # TypeScript configuration
├── package.json             # Dependencies
└── README.md                # Project documentation
```

## Building

### Development Build

```bash
# Build with debug symbols
npm run tauri:build:debug

# Output in src-tauri/target/debug/
```

### Production Build

```bash
# Build optimized release
npm run tauri:build

# Outputs:
# Linux:
#   - dist/phoenix-control-center_*.AppImage
#   - dist/phoenix-control-center_*.deb
# macOS:
#   - dist/Phoenix Control Center.app
# Windows:
#   - dist/Phoenix Control Center.exe
```

### Build Configuration

Edit `tauri.conf.json` to customize:

```json
{
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev",
    "devPath": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "Phoenix Control Center",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600
      }
    ]
  },
  "tauri": {
    "bundle": {
      "targets": ["deb", "appimage"]
    }
  }
}
```

## Testing

### Unit Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- src/components/Sidebar.test.tsx
```

### Integration Tests

```bash
# Test Tauri integration
npm run test -- src/services/systemService.test.ts
```

### UI Testing

```bash
# Start Vitest UI
npm run test:ui

# Opens browser at http://localhost:51204
```

### Coverage Report

```bash
# Generate coverage
npm run test:coverage

# View coverage report
open coverage/index.html
```

## Debugging

### Browser DevTools

```bash
# In development, press:
# - F12 or Ctrl+Shift+I to open DevTools
# - Ctrl+R to reload
# - Ctrl+Shift+R to hard reload
```

### Console Logging

```typescript
// In React components
console.log('Debug message:', data);

// In Tauri backend
println!("Debug message: {:?}", data);
```

### VS Code Debugging

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "attach",
      "name": "Attach to Tauri",
      "port": 9222,
      "pathMapping": {
        "/": "${workspaceRoot}",
        "/src": "${workspaceRoot}/src"
      }
    }
  ]
}
```

## Performance Optimization

### Bundle Size

```bash
# Analyze bundle size
npm run build
npm install -g source-map-explorer
source-map-explorer 'dist/**/*.js'
```

### Runtime Performance

1. **Use React DevTools Profiler**
   - Identify slow components
   - Check re-render frequency
   - Optimize with useMemo/useCallback

2. **Lazy Load Components**
   ```typescript
   const Dashboard = lazy(() => import('@pages/Dashboard'));
   ```

3. **Optimize Zustand Stores**
   - Use selectors for granular updates
   - Avoid creating new objects in selectors

4. **Memoize Expensive Computations**
   ```typescript
   const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
   ```

## Troubleshooting

### Common Issues

#### "Cannot find module '@tauri-apps/api'"

```bash
# Reinstall Tauri
npm install @tauri-apps/api --save
npm install @tauri-apps/cli --save-dev
```

#### "Vite dev server not starting"

```bash
# Check if port 5173 is in use
lsof -i :5173

# Kill process if needed
kill -9 <PID>

# Try different port
npm run dev -- --port 5174
```

#### "Tauri window won't open"

```bash
# Check Tauri logs
RUST_LOG=debug npm run tauri:dev

# Verify Rust installation
rustc --version
cargo --version
```

#### "Build fails with permission denied"

```bash
# Ensure proper permissions
chmod +x src-tauri/target/release/phoenix-control-center

# Or rebuild
npm run tauri:build -- --force
```

### Getting Help

1. **Check Logs**
   ```bash
   # Tauri logs
   cat ~/.local/share/phoenix-control-center/logs/

   # Browser console
   F12 → Console tab
   ```

2. **Enable Debug Mode**
   ```bash
   RUST_LOG=debug npm run tauri:dev
   ```

3. **Search Issues**
   - GitHub Issues: https://github.com/Bboy9090/phoenix-os/issues
   - Tauri Docs: https://tauri.app/docs/

## Environment Variables

Create `.env` file in project root:

```env
# Development
VITE_API_URL=http://localhost:8000
VITE_LOG_LEVEL=debug

# Production
VITE_API_URL=https://api.phoenix-os.com
VITE_LOG_LEVEL=error
```

Access in code:

```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push to remote
git push origin feature/new-feature

# Create Pull Request on GitHub
```

## Deployment

### Linux (.deb package)

```bash
# Build .deb
npm run tauri:build

# Install
sudo dpkg -i dist/phoenix-control-center_*.deb

# Run
phoenix-control-center
```

### AppImage

```bash
# Build AppImage
npm run tauri:build

# Make executable
chmod +x dist/phoenix-control-center_*.AppImage

# Run
./dist/phoenix-control-center_*.AppImage
```

## Resources

- **Tauri Documentation:** https://tauri.app/docs/
- **React Documentation:** https://react.dev/
- **Tailwind CSS:** https://tailwindcss.com/docs
- **Zustand:** https://github.com/pmndrs/zustand
- **Vite:** https://vitejs.dev/guide/

## Support

- **Issues:** https://github.com/Bboy9090/phoenix-os/issues
- **Discussions:** https://github.com/Bboy9090/phoenix-os/discussions
- **Email:** support@phoenix-os.com

## License

GNU General Public License v3.0

---

**Last Updated:** May 11, 2026  
**Version:** 2.0.0  
**Maintainer:** Phoenix OS Team

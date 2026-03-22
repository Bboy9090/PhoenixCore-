# Project TODO

- [x] Update theme colors to Phoenix Orange brand palette
- [x] Add tab bar icons mapping for all 4 tabs (Home, Device Wizard, USB Builder, Knowledge Base)
- [x] Configure tab navigation with 4 tabs
- [x] Build Home screen with hero section, feature cards, and stats
- [x] Build Device Wizard screen with step-by-step device identification flow
- [x] Build USB Builder screen with OS and tool catalog, toggle selection, size estimation
- [x] Build Knowledge Base screen with searchable article list
- [x] Create OS and Tool catalog data file
- [x] Create Device compatibility database
- [x] Create Knowledge Base articles data
- [x] Build OS Detail sub-screen (integrated into USB Builder)
- [x] Build Tool Detail sub-screen (integrated into USB Builder)
- [x] Build Device Compatibility Result sub-screen (integrated into Wizard)
- [x] Build Recipe Export functionality
- [x] Build Article Detail sub-screen
- [ ] Implement AsyncStorage persistence for recipes and bookmarks (future)
- [x] Generate custom app logo
- [x] Update app.config.ts with branding
- [x] Final polish and testing (15/15 unit tests passing)
- [x] Rebrand app to "Bobby's PhoenixDrive"
- [x] Update app.config.ts with new app name
- [x] Update Home screen hero text and branding
- [x] Optimize icon files for deployment (resize under 1MB)


## Phase 2: Backend API & PhoenixCore Integration

- [x] Create Flask backend API wrapper around PhoenixCore modules
- [x] Build hardware detection endpoint (/api/v1/hardware/detect)
- [x] Build USB device enumeration endpoint (/api/v1/usb/devices)
- [x] Build recipe building endpoint (/api/v1/recipe/build)
- [x] Build USB build execution endpoint (/api/v1/usb/build)
- [x] Build safety validation endpoint (/api/v1/safety/validate)
- [x] Implement WebSocket progress streaming for builds
- [x] Create React hooks for API interaction (use-phoenix-api.ts)
- [x] Integrate real hardware detection into Device Wizard (wizard-integrated.tsx)
- [x] Integrate real USB device enumeration into USB Builder (builder-integrated.tsx)
- [x] Integrate real recipe building into USB Builder
- [x] Add real-time build progress tracking to UI
- [x] Build desktop recipe consumer application (PhoenixDrive_Desktop_Consumer.py)
- [x] Add QR code generation for recipe export (qr-utils.ts)
- [x] Add QR code scanning for recipe import (recipe-export.tsx)
- [ ] Test end-to-end integration (mobile → backend → desktop)
- [ ] Add error handling and retry logic
- [ ] Add offline fallback mode

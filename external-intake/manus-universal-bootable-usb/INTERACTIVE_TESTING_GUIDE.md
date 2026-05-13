# Bobby's PhoenixDrive — Interactive Testing Guide

## Overview

This guide provides step-by-step instructions for manually testing every button, screen, and interaction in the mobile app. Use this before publishing to ensure all functionality works flawlessly.

---

## Pre-Test Setup

1. **Start the app** in Expo Go
2. **Have a test USB drive** connected (optional, for USB Builder testing)
3. **Backend API running** (optional, for real hardware detection)
4. **Test device** with various screen sizes (portrait orientation)

---

## Tab 1: Home Screen

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| "Start Building" | Navigate to USB Builder tab | [ ] |
| "Device Wizard" card | Navigate to Device Wizard tab | [ ] |
| "USB Builder" card | Navigate to USB Builder tab | [ ] |
| "Knowledge Base" card | Navigate to Knowledge Base tab | [ ] |

### Visual Elements to Verify

| Element | Expected | Status |
|---------|----------|--------|
| Phoenix logo displays | Orange phoenix icon visible | [ ] |
| Hero text readable | "Any Device. Any OS. Fixed." visible | [ ] |
| Feature cards render | 4 cards showing stats | [ ] |
| OS icons display | All OS icons visible in grid | [ ] |
| Colors correct | Phoenix Orange (#FF8C00) theme | [ ] |
| Text contrast | All text readable on background | [ ] |
| Responsive layout | Content fits on small/large screens | [ ] |

### Navigation Test

- [ ] Tap "Start Building" → goes to USB Builder
- [ ] Tap "Device Wizard" card → goes to Device Wizard
- [ ] Tap "USB Builder" card → goes to USB Builder
- [ ] Tap "Knowledge Base" card → goes to Knowledge Base
- [ ] Swipe left → goes to next tab
- [ ] Swipe right → goes to previous tab
- [ ] Tap tab bar icons → switches tabs

---

## Tab 2: Device Wizard

### Step 1: Device Detection

| Element | Expected | Status |
|---------|----------|--------|
| Loading indicator | Shows while detecting | [ ] |
| CPU info | Displays processor name | [ ] |
| Memory info | Shows RAM amount | [ ] |
| Storage info | Shows disk size | [ ] |
| Architecture | Shows x86_64, arm64, etc. | [ ] |

### Step 2: Compatibility Matrix

| Element | Expected | Status |
|---------|----------|--------|
| Compatible OSes | Listed with green checkmark | [ ] |
| Incompatible OSes | Listed with red X and reason | [ ] |
| Partial support | Shown with yellow warning | [ ] |
| Explanations | Clear reasons for incompatibility | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| "Detect Again" | Re-runs hardware detection | [ ] |
| "Next" | Goes to compatibility details | [ ] |
| "Back" | Returns to previous step | [ ] |
| OS compatibility item | Shows details about that OS | [ ] |

### Navigation Test

- [ ] Tap "Detect Again" → hardware detection runs
- [ ] Tap "Next" → shows compatibility matrix
- [ ] Tap OS item → shows details
- [ ] Tap "Back" → returns to detection
- [ ] Swipe back → returns to Home

---

## Tab 3: USB Builder

### Step 1: USB Device Selection

| Element | Expected | Status |
|--------|----------|--------|
| USB devices listed | Shows all connected USB drives | [ ] |
| Device size shown | Displays GB capacity | [ ] |
| Device health | Shows "healthy" or warning | [ ] |
| Device path | Shows /dev/sdb or similar | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| USB device item | Selects that device | [ ] |
| "Refresh" | Re-scans for USB devices | [ ] |
| "Next" | Goes to OS selection | [ ] |

### Step 2: OS Selection

| Element | Expected | Status |
|--------|----------|--------|
| OS list displays | Shows 10+ operating systems | [ ] |
| Toggle switches | Can toggle each OS on/off | [ ] |
| Size updates | Total size recalculates | [ ] |
| Compatibility shown | Compatible OSes highlighted | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| OS toggle | Adds/removes OS from recipe | [ ] |
| "OS Details" | Shows info about that OS | [ ] |
| "Next" | Goes to tool selection | [ ] |
| "Back" | Returns to device selection | [ ] |

### Step 3: Tool Selection

| Element | Expected | Status |
|--------|----------|--------|
| Tool list displays | Shows 7+ repair tools | [ ] |
| Toggle switches | Can toggle each tool on/off | [ ] |
| Size updates | Total size recalculates | [ ] |
| Descriptions shown | Tool descriptions visible | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| Tool toggle | Adds/removes tool from recipe | [ ] |
| "Tool Details" | Shows info about that tool | [ ] |
| "Next" | Goes to review | [ ] |
| "Back" | Returns to OS selection | [ ] |

### Step 4: Review

| Element | Expected | Status |
|--------|----------|--------|
| Recipe name shown | Displays recipe title | [ ] |
| OSes listed | Shows all selected OSes | [ ] |
| Tools listed | Shows all selected tools | [ ] |
| Total size shown | Displays total GB | [ ] |
| Fits on USB | Shows "✓ Fits" or "✗ Too large" | [ ] |
| Estimated time | Shows write time estimate | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| "Edit Recipe" | Returns to OS selection | [ ] |
| "Export" | Shows export options | [ ] |
| "Build USB" | Starts build process | [ ] |
| "Back" | Returns to tool selection | [ ] |

### Step 5: Build Progress

| Element | Expected | Status |
|--------|----------|--------|
| Progress bar | Animates from 0-100% | [ ] |
| Stage shown | Shows current operation | [ ] |
| Speed displayed | Shows MB/s write speed | [ ] |
| ETA shown | Shows time remaining | [ ] |
| Percentage updates | Updates every 1-2 seconds | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| "Cancel" | Stops build (if available) | [ ] |
| "Done" | Completes and returns to home | [ ] |

---

## Tab 4: Knowledge Base

### Search Functionality

| Element | Expected | Status |
|--------|----------|--------|
| Search bar | Accepts text input | [ ] |
| Search results | Filters articles as you type | [ ] |
| Clear button | Clears search text | [ ] |
| No results message | Shows when no matches | [ ] |

### Article List

| Element | Expected | Status |
|--------|----------|--------|
| Articles display | Shows 6+ articles | [ ] |
| Article titles | Readable and descriptive | [ ] |
| Article previews | Shows first 100 chars | [ ] |
| Category tags | Shows article category | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| Article item | Opens article detail | [ ] |
| Bookmark icon | Toggles bookmark on/off | [ ] |
| "Read More" | Opens full article | [ ] |
| Back button | Returns to article list | [ ] |

### Article Detail

| Element | Expected | Status |
|--------|----------|--------|
| Full article text | Displays complete content | [ ] |
| Readable formatting | Text properly formatted | [ ] |
| Bookmark button | Shows bookmark status | [ ] |
| Share button | Opens share dialog | [ ] |

### Buttons to Test

| Button | Expected Behavior | Status |
|--------|-------------------|--------|
| Bookmark icon | Toggles bookmark | [ ] |
| Share button | Opens system share menu | [ ] |
| Back button | Returns to article list | [ ] |

---

## Cross-Tab Features

### Recipe Persistence

- [ ] Build recipe in USB Builder
- [ ] Close app completely
- [ ] Reopen app
- [ ] Go to USB Builder
- [ ] Verify recipe is still there
- [ ] Can rebuild same USB

### Bookmarks Persistence

- [ ] Bookmark article in Knowledge Base
- [ ] Close app
- [ ] Reopen app
- [ ] Go to Knowledge Base
- [ ] Verify bookmark is still there
- [ ] Bookmarked article marked with filled icon

### Dark Mode

- [ ] Toggle system dark mode
- [ ] App switches to dark theme
- [ ] All text readable in dark mode
- [ ] Colors appropriate for dark mode
- [ ] No contrast issues

### Responsive Design

- [ ] Test on small phone (375px width)
- [ ] Test on large phone (428px width)
- [ ] Test on tablet (768px width)
- [ ] All content fits without horizontal scroll
- [ ] Buttons easily tappable
- [ ] Text readable at all sizes

---

## Error Handling Tests

### Network Errors

- [ ] Disconnect internet
- [ ] Try to detect hardware
- [ ] Verify error message shown
- [ ] Verify "Retry" button available
- [ ] Reconnect internet
- [ ] Tap "Retry" → should work

### Invalid USB Device

- [ ] Select USB device too small
- [ ] Try to add large recipe
- [ ] Verify error message
- [ ] Verify "Choose different device" option

### Storage Errors

- [ ] Fill up device storage (if possible)
- [ ] Try to save recipe
- [ ] Verify error message
- [ ] Verify recovery steps shown

---

## Performance Tests

| Test | Expected | Status |
|------|----------|--------|
| App launch time | < 3 seconds | [ ] |
| Tab switching | Instant | [ ] |
| Hardware detection | < 5 seconds | [ ] |
| USB enumeration | < 3 seconds | [ ] |
| Recipe building | < 10 seconds | [ ] |
| Search response | < 1 second | [ ] |
| Scroll smoothness | 60 FPS | [ ] |

---

## Accessibility Tests

| Test | Expected | Status |
|------|----------|--------|
| Text size readable | 14pt minimum | [ ] |
| Color contrast | WCAG AA standard | [ ] |
| Touch targets | 44pt minimum | [ ] |
| Screen reader | Works on all text | [ ] |
| Keyboard navigation | All features accessible | [ ] |
| Focus indicators | Visible on all buttons | [ ] |

---

## Final Checklist

Before publishing, verify:

- [ ] All buttons work
- [ ] All navigation works
- [ ] Recipes persist
- [ ] Bookmarks persist
- [ ] Dark mode works
- [ ] Responsive on all sizes
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] Error messages clear
- [ ] Performance acceptable
- [ ] Accessibility good
- [ ] All icons display
- [ ] All text readable
- [ ] No broken links
- [ ] Help text clear

---

## Known Issues

| Issue | Workaround | Status |
|-------|-----------|--------|
| | | |

---

## Sign-Off

| Tester | Date | Status |
|--------|------|--------|
| | | |


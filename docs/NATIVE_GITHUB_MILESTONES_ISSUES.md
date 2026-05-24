# Blue Phoenix Native: GitHub Milestones & Issues

This document defines the structured GitHub issue templates, Epic structures, and milestone tasks compiled to drive development for the **Blue Phoenix Native: Crown Edition** operating system.

---

## 🏛️ Master Epic Structure

```text
Title: epic(native): build Blue Phoenix Native Crown Edition app and game ecosystem
Labels: epic, sovereign-native, crown-edition
Description:
  This epic tracks the unified strategic roadmap to build the first from-scratch, 
  non-Linux operating system (Blue Phoenix Native) and compile its first-party 
  exclusives Crown Application Bundle and Games Suite.
```

---

## 🚀 Core Runtime Issues (Milestones NATIVE-1, NATIVE-2)

### 1. `feat(native): define Blue Phoenix Native app package format`
* **Labels:** native-core, packaging
* **Task:** Define the standard specifications for `.wpk` (WorldKit Package) files, including metadata formatting, binary signatures, and compressed asset directories structure.

### 2. `feat(native): create WorldKit SDK MVP`
* **Labels:** native-core, sdk
* **Task:** Code the initial Rust target bindings for custom GUI window construction, draw hooks, text rendering, and low-latency canvas clear commands.

### 3. `feat(native): implement native app launcher protocol`
* **Labels:** native-core, window-manager
* **Task:** Code standard DBus-style messages loops in the Citadel Compositor to process process spawns, window bindings, and focus state parameters.

### 4. `feat(native): implement app permissions and manifest model`
* **Labels:** native-core, security
* **Task:** Enforce sandbox containment filters, matching dynamic user-request capabilities (network client, SMART sector reads) against the security rules of **PR34**.

---

## 🛠️ Flagship Application Issues (Milestone NATIVE-4)

### 1. `feat(command): port Command to Blue Phoenix Native`
* **Labels:** app-command, sovereign-native
* **Task:** Extract portable console logic traits from `apps/cli/` and bind them to the WorldKit native layout libraries, compiling a secure native terminal tool.

### 2. `feat(market): port Market to Blue Phoenix Native`
* **Labels:** app-market, sovereign-native
* **Task:** Build a native software catalog browser drawing the flagship store layout natively on VGA frames using standard double-buffered structures.

### 3. `feat(harbor): build native file manager MVP`
* **Labels:** app-harbor, sovereign-native
* **Task:** Port the secure directory layout scanner to standard WorldKit canvas components, providing dynamic read-only filesystem lists.

---

## 🎮 First-Party Games Issues (Milestone NATIVE-5)

### 1. `feat(thunder-runner): build native platformer MVP`
* **Labels:** game-runner, sovereign-native
* **Task:** Build a 2D side-scrolling physics loop rendering wireframe character physics and checking low-latency audio soundtracks.

### 2. `feat(storm-grid): build native puzzle strategy MVP`
* **Labels:** game-grid, sovereign-native
* **Task:** Code a grid logic puzzle game utilizing custom vector glow shaders and responsive touch controls.

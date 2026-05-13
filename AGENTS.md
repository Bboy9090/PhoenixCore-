# AGENTS.md

## Phoenix Platform Rules

This repository is a long-term operating-system platform project.

Agents must follow these rules strictly.

## Allowed Actions

* Documentation
* Route integration
* Navigation fixes
* Typed SDK generation
* Contract scaffolding
* Test scaffolding
* Build verification
* Lint/typecheck fixes
* README updates
* Migration notes
* Safe placeholder UI generation

## Forbidden Actions

* No recursive deletion
* No destructive git operations
* No mass source moves
* No architecture rewrites
* No replacing canonical stack decisions
* No changing product naming doctrine
* No direct disk/system destructive logic
* No removal of legacy source without archive documentation
* No changing Phoenix OS manifesto without explicit approval

## Canonical Stack

Desktop:

* Tauri
* React
* TypeScript
* Tailwind
* Rust

Mobile:

* Expo React Native

Web:

* Next.js

OS:

* KDE Plasma
* Debian/Ubuntu base
* Wayland-first

## Canonical Products

* Phoenix Platform
* Phoenix OS
* Phoenix Control Center
* Phoenix Agent
* BootForge
* Phoenix Key

## Safety Doctrine

UI apps may never directly perform destructive disk/system operations.

All dangerous operations must pass through:

1. Phoenix Agent
2. Rust safety gates

## Current Phase

Infrastructure stabilization and contract mapping.

Do NOT perform broad migrations or architecture rewrites.

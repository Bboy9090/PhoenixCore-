import SwiftUI
import AppKit
import UniformTypeIdentifiers

enum StudioModule: String, CaseIterable, Identifiable {
    case matrixAndDoctor = "Connection Matrix & Doctor"
    #if STORE_EDITION
    case ownerProVault = "BobFWTools Pro Suite"
    #else
    case ownerProVault = "Owner Pro Vault (Unlocked)"
    #endif
    case samsung = "Samsung Servicing & Odin"
    case multiBrandRecovery = "MTK / SPD / EDL & Multi-Brand"
    case fastboot = "Fastboot & Partitions"
    case developerWorkbench = "Developer Workbench & Logcat"
    case firmware = "Firmware & Inventory Ledger"
    case apple = "Apple / iDevice Recovery"
    case jobsAndBridge = "Audit Jobs, Notes & VM Bridge"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .matrixAndDoctor: return "point.3.connected.trianglepath.dotted"
        case .ownerProVault: return "crown.fill"
        case .samsung: return "cpu.fill"
        case .multiBrandRecovery: return "wrench.and.screwdriver.fill"
        case .fastboot: return "bolt.horizontal.circle.fill"
        case .developerWorkbench: return "terminal.fill"
        case .firmware: return "shippingbox.fill"
        case .apple: return "iphone"
        case .jobsAndBridge: return "checkmark.shield.fill"
        }
    }
}

enum StudioTheme {
    static let obsidianBg = Color(red: 0.039, green: 0.051, blue: 0.078)       // #0A0D14
    static let railBg = Color(red: 0.051, green: 0.067, blue: 0.102)           // #0D111A
    static let surfaceCard = Color(red: 0.067, green: 0.086, blue: 0.133)      // #111622
    static let surfaceElevated = Color(red: 0.090, green: 0.118, blue: 0.180)  // #171E2E
    static let cyanAccent = Color(red: 0.0, green: 0.898, blue: 1.0)           // #00E5FF
    static let amberAccent = Color(red: 1.0, green: 0.702, blue: 0.0)          // #FFB300
    static let borderSubtle = Color.white.opacity(0.08)
    static let borderCyan = Color(red: 0.0, green: 0.898, blue: 1.0).opacity(0.28)

    static func bundleImage(_ resourceName: String) -> NSImage? {
        if let url = Bundle.main.url(forResource: resourceName, withExtension: "png") {
            return NSImage(contentsOf: url)
        }
        return nil
    }
}

struct StudioLaunchSplashOverlay: View {
    let onDismiss: () -> Void
    @State private var pulse = false

    var body: some View {
        ZStack {
            StudioTheme.obsidianBg.ignoresSafeArea()

            if let hero = StudioTheme.bundleImage("SplashHero") {
                Image(nsImage: hero)
                    .resizable()
                    .scaledToFill()
                    .opacity(0.42)
                    .ignoresSafeArea()
            }

            LinearGradient(
                colors: [
                    StudioTheme.obsidianBg.opacity(0.85),
                    StudioTheme.obsidianBg.opacity(0.55),
                    StudioTheme.obsidianBg.opacity(0.95)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 22) {
                if let icon = StudioTheme.bundleImage("AppIcon_1024") {
                    Image(nsImage: icon)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 118, height: 118)
                        .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 26, style: .continuous)
                                .stroke(
                                    LinearGradient(colors: [StudioTheme.cyanAccent.opacity(0.7), StudioTheme.amberAccent.opacity(0.5)], startPoint: .topLeading, endPoint: .bottomTrailing),
                                    lineWidth: 1.5
                                )
                        )
                        .shadow(color: StudioTheme.cyanAccent.opacity(pulse ? 0.45 : 0.2), radius: 28)
                }

                VStack(spacing: 6) {
                    Text("BOBFWTOOLS STUDIO")
                        .font(.system(size: 26, weight: .heavy, design: .rounded))
                        .tracking(2.2)
                        .foregroundStyle(
                            LinearGradient(colors: [.white, StudioTheme.cyanAccent], startPoint: .leading, endPoint: .trailing)
                        )
                    Text("PHOENIX FORGE · NATIVE MACOS HARDWARE WORKBENCH")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(1.6)
                        .foregroundColor(StudioTheme.amberAccent.opacity(0.92))
                }

                HStack(spacing: 10) {
                    ProgressView()
                        .controlSize(.small)
                        .tint(StudioTheme.cyanAccent)
                    Text("Arming IOKit USB Hotplug & BootForge Engine...")
                        .font(.system(size: 11.5, weight: .medium, design: .monospaced))
                        .foregroundColor(.white.opacity(0.82))
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    Capsule()
                        .fill(StudioTheme.surfaceElevated.opacity(0.85))
                        .overlay(Capsule().stroke(StudioTheme.borderCyan, lineWidth: 1))
                )
            }
            .padding(40)
        }
        .contentShape(Rectangle())
        .onTapGesture { onDismiss() }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.1).repeatForever(autoreverses: true)) {
                pulse = true
            }
        }
    }
}

struct MainStudioView: View {
    @StateObject private var engine = ServicingEngine()
    @State private var selectedModule: StudioModule = .matrixAndDoctor
    @State private var customCommand: String = ""
    @State private var showLaunchSplash: Bool = true

    var body: some View {
        ZStack {
            StudioTheme.obsidianBg.ignoresSafeArea()

            VStack(spacing: 0) {
                TopHardwareBar(engine: engine)
                if let modemInfo = engine.samsungModemInfo {
                    SamsungLiveIdentityBanner(info: modemInfo)
                } else if engine.activePlatform == .appleIos || engine.detectedAppleMode != .none {
                    AppleLiveIdentityBanner(engine: engine) {
                        selectedModule = .apple
                    }
                }
                Rectangle()
                    .fill(StudioTheme.borderSubtle)
                    .frame(height: 1)

                HSplitView {
                    // Left Navigation + Active Module Workspace
                    HStack(spacing: 0) {
                        VStack(alignment: .leading, spacing: 5) {
                            Text("BOBFWTOOLS WORKSPACE")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .tracking(1.1)
                                .foregroundColor(StudioTheme.cyanAccent.opacity(0.8))
                                .padding(.horizontal, 12)
                                .padding(.top, 12)
                                .padding(.bottom, 2)

                            ForEach(StudioModule.allCases) { module in
                                let isTargetMatched: Bool = {
                                    switch module {
                                    case .samsung: return engine.activePlatform == .samsung
                                    case .apple: return engine.activePlatform == .appleIos
                                    case .fastboot, .multiBrandRecovery: return engine.activePlatform == .genericAndroid
                                    case .developerWorkbench: return engine.activePlatform == .genericAndroid || engine.activePlatform == .samsung
                                    default: return true
                                    }
                                }()
                                let isSelected = selectedModule == module

                                Button {
                                    selectedModule = module
                                } label: {
                                    HStack(spacing: 8) {
                                        RoundedRectangle(cornerRadius: 2)
                                            .fill(isSelected ? StudioTheme.cyanAccent : Color.clear)
                                            .frame(width: 3, height: 18)

                                        Image(systemName: module.icon)
                                            .frame(width: 18)
                                            .foregroundColor(isSelected ? StudioTheme.cyanAccent : (isTargetMatched ? .white.opacity(0.88) : .secondary.opacity(0.55)))
                                        Text(module.rawValue)
                                            .font(.system(size: 12.5, weight: isSelected ? .semibold : .regular))
                                            .lineLimit(1)
                                        Spacer()
                                        if isTargetMatched && engine.activePlatform != .none && [.samsung, .apple, .fastboot].contains(module) {
                                            Text("ACTIVE")
                                                .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                                                .padding(.horizontal, 5)
                                                .padding(.vertical, 1.5)
                                                .background(RoundedRectangle(cornerRadius: 3).fill(Color.green.opacity(0.22)))
                                                .foregroundColor(.green)
                                        } else if !isTargetMatched && [.samsung, .apple].contains(module) {
                                            Text("IDLE")
                                                .font(.system(size: 8, weight: .semibold, design: .monospaced))
                                                .foregroundColor(.secondary.opacity(0.5))
                                        }
                                    }
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 7)
                                    .background(
                                        RoundedRectangle(cornerRadius: 8)
                                            .fill(isSelected ? StudioTheme.cyanAccent.opacity(0.14) : Color.clear)
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 8)
                                                    .stroke(isSelected ? StudioTheme.borderCyan : Color.clear, lineWidth: 1)
                                            )
                                    )
                                    .foregroundColor(isSelected ? .white : (isTargetMatched ? .white.opacity(0.85) : .secondary.opacity(0.7)))
                                }
                                .buttonStyle(.plain)
                            }

                            Spacer()

                            VStack(alignment: .leading, spacing: 5) {
                                Text("NATIVE ENGINE STATUS")
                                    .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                    .tracking(0.8)
                                    .foregroundColor(StudioTheme.amberAccent.opacity(0.85))
                                BackendBadge(name: "BootForge USB (rusb)", path: engine.bootforgeBinaryPath)
                                BackendBadge(name: "Samsung Modem (AT)", path: engine.selectedSerialPort.isEmpty ? "/dev/cu.SAMSUNG_MDM" : engine.selectedSerialPort, isDeviceNode: true)
                                BackendBadge(name: "Android ADB", path: engine.toolPaths["adb"]!)
                                BackendBadge(name: "Fastboot", path: engine.toolPaths["fastboot"]!)
                                BackendBadge(name: "Heimdall (Odin)", path: engine.toolPaths["heimdall"]!)
                                BackendBadge(name: "libimobiledevice", path: engine.toolPaths["ideviceinfo"]!)
                            }
                            .padding(10)
                            .background(
                                RoundedRectangle(cornerRadius: 10)
                                    .fill(StudioTheme.surfaceCard)
                                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(StudioTheme.borderSubtle, lineWidth: 1))
                            )
                        }
                        .padding(10)
                        .frame(width: 254)
                        .background(StudioTheme.railBg)

                        Rectangle()
                            .fill(StudioTheme.borderSubtle)
                            .frame(width: 1)

                        // Active Module Content Area
                        ScrollView {
                            VStack(alignment: .leading, spacing: 18) {
                                switch selectedModule {
                                case .matrixAndDoctor:
                                    ConnectionMatrixAndDoctorView(engine: engine)
                                case .ownerProVault:
                                    OwnerProVaultView(engine: engine)
                                case .samsung:
                                    SamsungSuiteView(engine: engine)
                                case .multiBrandRecovery:
                                    MultiBrandRecoveryView(engine: engine)
                                case .fastboot:
                                    FastbootWorkshopView(engine: engine)
                                case .developerWorkbench:
                                    DeveloperWorkbenchView(engine: engine)
                                case .firmware:
                                    FirmwareInspectorView(engine: engine)
                                case .apple:
                                    AppleServicingView(engine: engine)
                                case .jobsAndBridge:
                                    JobsNotesAndBridgeView(engine: engine)
                                }
                            }
                            .padding(20)
                        }
                        .background(StudioTheme.obsidianBg)
                        .frame(minWidth: 540, maxWidth: .infinity)
                    }

                    // Right Console Output Panel
                    ConsoleLogPanel(engine: engine, customCommand: $customCommand)
                        .frame(minWidth: 360, idealWidth: 430)
                        .background(StudioTheme.railBg)
                }
            }

            if showLaunchSplash {
                StudioLaunchSplashOverlay {
                    withAnimation(.easeOut(duration: 0.35)) {
                        showLaunchSplash = false
                    }
                }
                .transition(.opacity)
                .zIndex(50)
            }
        }
        .preferredColorScheme(.dark)
        .frame(minWidth: 1180, minHeight: 740)
        .task {
            try? await Task.sleep(nanoseconds: 1_750_000_000)
            await MainActor.run {
                withAnimation(.easeOut(duration: 0.45)) {
                    showLaunchSplash = false
                }
            }
        }
    }
}

// MARK: - Top Hardware Bar & Live Samsung Identity Banner

struct TopHardwareBar: View {
    @ObservedObject var engine: ServicingEngine

    var gradeColor: Color {
        switch engine.connectionGrade {
        case "EXCELLENT": return .green
        case "USABLE": return StudioTheme.cyanAccent
        case "NONE": return StudioTheme.amberAccent
        default: return .secondary
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            HStack(spacing: 10) {
                if let icon = StudioTheme.bundleImage("AppIcon_1024") {
                    Image(nsImage: icon)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 30, height: 30)
                        .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 7, style: .continuous)
                                .stroke(StudioTheme.borderCyan, lineWidth: 1)
                        )
                } else {
                    Image(systemName: "cpu.fill")
                        .font(.system(size: 20))
                        .foregroundColor(StudioTheme.cyanAccent)
                }
                VStack(alignment: .leading, spacing: 1) {
                    Text("BobFWTools Studio")
                        .font(.system(size: 13.5, weight: .bold))
                        .foregroundColor(.white)
                    Text("Phoenix Forge · Hardware & Firmware Workbench")
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(StudioTheme.cyanAccent.opacity(0.8))
                }
            }

            Divider().frame(height: 28)

            // Active Device Picker
            HStack(spacing: 6) {
                Text("Target:")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.secondary)

                Picker("", selection: $engine.selectedDevice) {
                    if engine.devices.isEmpty {
                        Text("No Device Connected").tag(Optional<ConnectedDevice>.none)
                    }
                    ForEach(engine.devices) { dev in
                        Text("[\(dev.transport.rawValue)] \(dev.name)").tag(Optional(dev))
                    }
                }
                .frame(width: 260)
            }

            // Serial / Modem Port Picker
            HStack(spacing: 6) {
                Text("Modem:")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.secondary)

                Picker("", selection: $engine.selectedSerialPort) {
                    if engine.serialPorts.isEmpty {
                        Text("No /dev/cu.SAMSUNG*").tag("")
                    }
                    ForEach(engine.serialPorts, id: \.self) { port in
                        Text((port as NSString).lastPathComponent).tag(port)
                    }
                }
                .frame(width: 185)
            }

            Button {
                Task { await engine.refreshDevicesAndTelemetry() }
            } label: {
                Label("Scan Bus", systemImage: "arrow.clockwise")
            }
            .disabled(engine.isBusy)

            Button {
                Task { await engine.runUsbCableDoctor() }
            } label: {
                Label("Cable Doctor", systemImage: "stethoscope")
            }
            .disabled(engine.isBusy)

            Spacer()

            if let match = engine.universalMatch {
                HStack(spacing: 6) {
                    Image(systemName: match.platform.badgeIcon)
                        .foregroundColor(.green)
                    Text("MATCH: \(match.modelNumber) · \(match.securityBitOrIosVer) · Stock: \(match.stockFirmwareBuild) · CSC: \(match.carrierCscOrRegion.components(separatedBy: " ").first ?? "OPEN")")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundColor(.green)
                        .lineLimit(1)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color.green.opacity(0.12)))
            }

            #if STORE_EDITION
            Text(engine.isProUnlocked ? "STORE PRO LICENSE ACTIVE" : "FREE TIER (STORE EDITION)")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(RoundedRectangle(cornerRadius: 6).fill((engine.isProUnlocked ? Color.purple : Color.orange).opacity(0.18)))
                .foregroundColor(engine.isProUnlocked ? .purple : .orange)
            #else
            Text("OWNER PRIVATE COPY · ALL UNLOCKED")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color.purple.opacity(0.18)))
                .foregroundColor(.purple)
            #endif

            Text("LINK: \(engine.connectionGrade)")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(RoundedRectangle(cornerRadius: 6).fill(gradeColor.opacity(0.18)))
                .foregroundColor(gradeColor)

            if engine.isBusy {
                ProgressView()
                    .controlSize(.small)
            }
        }
        .padding(.horizontal, 16)
        .padding(.top, 28)
        .padding(.bottom, 10)
        .background(StudioTheme.railBg)
    }
}

struct SamsungLiveIdentityBanner: View {
    let info: SamsungDevConInfo

    var body: some View {
        HStack(spacing: 16) {
            Label("VERIFIED SAMSUNG TARGET", systemImage: "checkmark.seal.fill")
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(.green)

            BannerPair(label: "Model", value: info.model)
            BannerPair(label: "PDA / Build", value: info.pdaVersion)
            BannerPair(label: "CSC", value: "\(info.activeCsc) (\(info.countryCode))")
            BannerPair(label: "Serial", value: info.serialNumber)
            BannerPair(label: "Lock", value: info.carrierLock)
            BannerPair(label: "Transports", value: info.activeTransports)
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(Color.green.opacity(0.08))
    }
}

struct AppleLiveIdentityBanner: View {
    @ObservedObject var engine: ServicingEngine
    var onSelectAppleModule: (() -> Void)? = nil

    private var targetTitle: String {
        let dev = engine.devices.first { $0.transport == .ios }
        if let name = dev?.name, !name.isEmpty { return name }
        if !engine.lastObservedRecoveryProduct.isEmpty { return "Apple \(engine.lastObservedRecoveryProduct)" }
        return "Apple iDevice"
    }

    private var targetSerial: String {
        let dev = engine.devices.first { $0.transport == .ios }
        return dev?.serial ?? (engine.deviceProperties["SerialNumber"] ?? "USB Serial Standby")
    }

    private var modeString: String {
        engine.detectedAppleMode.rawValue
    }

    var body: some View {
        HStack(spacing: 16) {
            Label("VERIFIED APPLE TARGET", systemImage: "applelogo")
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(.indigo)

            BannerPair(label: "Device", value: targetTitle)
            BannerPair(label: "Mode", value: modeString)
            BannerPair(label: "Identifier", value: engine.lastObservedRecoveryProduct.isEmpty ? (engine.deviceProperties["ProductType"] ?? "Apple iDevice") : engine.lastObservedRecoveryProduct)
            BannerPair(label: "Serial/ECID", value: targetSerial)

            Spacer()

            if let onSelect = onSelectAppleModule {
                Button("Open Apple Restorer") {
                    onSelect()
                }
                .font(.system(size: 10.5, weight: .bold))
                .buttonStyle(.borderedProminent)
                .tint(.indigo)
                .controlSize(.small)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(Color.indigo.opacity(0.08))
    }
}

struct BannerPair: View {
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 4) {
            Text("\(label):")
                .font(.system(size: 11))
                .foregroundColor(.secondary)
            Text(value.isEmpty ? "N/A" : value)
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
        }
    }
}

struct BackendBadge: View {
    let name: String
    let path: String
    var isDeviceNode: Bool = false

    var isInstalled: Bool {
        if isDeviceNode {
            return FileManager.default.fileExists(atPath: path)
        }
        return FileManager.default.isExecutableFile(atPath: path)
    }

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(isInstalled ? Color.green : Color.orange)
                .frame(width: 7, height: 7)
            Text(name)
                .font(.system(size: 11, weight: .medium))
            Spacer()
            Text(isInstalled ? "Active" : "Standby")
                .font(.system(size: 10))
                .foregroundColor(.secondary)
        }
    }
}

// MARK: - Reusable Guided Step-by-Step State Machine Wizard View

struct GuidedWorkflowWizardCard: View {
    let title: String
    let subtitle: String
    let icon: String
    let steps: [GuidedPipelineStep]
    let onExecuteStep: (Int) -> Void
    let onReset: () -> Void

    var body: some View {
        GroupBox(label: Label(title, systemImage: icon)) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text(subtitle)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                    Spacer()
                    Button("Reset Pipeline", action: onReset)
                        .controlSize(.small)
                }

                VStack(spacing: 8) {
                    ForEach(steps) { step in
                        VStack(alignment: .leading, spacing: 6) {
                            HStack(alignment: .center, spacing: 10) {
                                // Step indicator circle
                                ZStack {
                                    Circle()
                                        .fill(stepBadgeBackground(step.state))
                                        .frame(width: 24, height: 24)
                                    Text("\(step.stepNumber)")
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        .foregroundColor(stepBadgeTextColor(step.state))
                                }

                                VStack(alignment: .leading, spacing: 2) {
                                    HStack(spacing: 6) {
                                        Text(step.title)
                                            .font(.system(size: 12, weight: .semibold))
                                        Text("[\(step.requiredTransport.rawValue)]")
                                            .font(.system(size: 9.5, weight: .medium, design: .monospaced))
                                            .padding(.horizontal, 5)
                                            .padding(.vertical, 1)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(Color.secondary.opacity(0.15)))
                                            .foregroundColor(.secondary)
                                    }
                                    Text(step.detail)
                                        .font(.system(size: 11))
                                        .foregroundColor(.secondary)
                                }

                                Spacer()

                                // State badge
                                Text(step.state.rawValue)
                                    .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(RoundedRectangle(cornerRadius: 4).fill(stepBadgeBackground(step.state)))
                                    .foregroundColor(stepBadgeTextColor(step.state))

                                // Action Button
                                Button {
                                    onExecuteStep(step.stepNumber)
                                } label: {
                                    HStack(spacing: 4) {
                                        if step.state == .running {
                                            ProgressView().controlSize(.mini)
                                        } else if step.state == .succeeded {
                                            Image(systemName: "checkmark")
                                        } else if step.state == .locked {
                                            Image(systemName: "lock.fill")
                                        } else if step.state == .failed {
                                            Image(systemName: "arrow.clockwise")
                                        }
                                        Text(buttonLabel(for: step))
                                    }
                                }
                                .controlSize(.small)
                                .buttonStyle(.bordered)
                                .disabled(step.state == .locked || step.state == .running || step.state == .succeeded)
                            }

                            // Technician Action Callout
                            if let action = step.technicianAction, (step.state == .ready || step.state == .failed) {
                                HStack(spacing: 6) {
                                    Image(systemName: "hand.tap.fill")
                                        .font(.system(size: 11))
                                        .foregroundColor(.orange)
                                    Text("Technician Action: \(action)")
                                        .font(.system(size: 10.5, weight: .medium))
                                        .foregroundColor(.orange)
                                }
                                .padding(.leading, 34)
                            }

                            // Evidence Box
                            if let ev = step.resultEvidence, !ev.isEmpty {
                                HStack(alignment: .top, spacing: 6) {
                                    Image(systemName: step.state == .succeeded ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                                        .font(.system(size: 10))
                                        .foregroundColor(step.state == .succeeded ? .green : .red)
                                    Text(ev)
                                        .font(.system(size: 10, design: .monospaced))
                                        .foregroundColor(.primary)
                                        .lineLimit(2)
                                }
                                .padding(6)
                                .background(RoundedRectangle(cornerRadius: 4).fill(Color(NSColor.controlBackgroundColor)))
                                .padding(.leading, 34)
                            }
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.windowBackgroundColor)))
                    }
                }
            }
            .padding(8)
        }
    }

    private func buttonLabel(for step: GuidedPipelineStep) -> String {
        switch step.state {
        case .locked: return "Locked"
        case .ready: return "Execute Step \(step.stepNumber)"
        case .running: return "Running..."
        case .succeeded: return "Passed"
        case .failed: return "Retry Step \(step.stepNumber)"
        }
    }

    private func stepBadgeBackground(_ state: PipelineStepState) -> Color {
        switch state {
        case .locked: return Color.secondary.opacity(0.2)
        case .ready: return Color.blue.opacity(0.2)
        case .running: return Color.orange.opacity(0.25)
        case .succeeded: return Color.green.opacity(0.2)
        case .failed: return Color.red.opacity(0.2)
        }
    }

    private func stepBadgeTextColor(_ state: PipelineStepState) -> Color {
        switch state {
        case .locked: return .secondary
        case .ready: return .blue
        case .running: return .orange
        case .succeeded: return .green
        case .failed: return .red
        }
    }
}

// MARK: - Module 1: BobFWTools Connection Matrix & USB Cable Doctor

struct StudioWorkbenchHeroBanner: View {
    @ObservedObject var engine: ServicingEngine

    var body: some View {
        ZStack(alignment: .leading) {
            if let hero = StudioTheme.bundleImage("SplashHero") {
                Image(nsImage: hero)
                    .resizable()
                    .scaledToFill()
                    .frame(height: 112)
                    .clipped()
                    .opacity(0.35)
            }

            LinearGradient(
                colors: [
                    StudioTheme.surfaceCard.opacity(0.94),
                    StudioTheme.surfaceCard.opacity(0.76),
                    StudioTheme.obsidianBg.opacity(0.88)
                ],
                startPoint: .leading,
                endPoint: .trailing
            )

            HStack(spacing: 16) {
                if let icon = StudioTheme.bundleImage("AppIcon_1024") {
                    Image(nsImage: icon)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 64, height: 64)
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .stroke(StudioTheme.borderCyan, lineWidth: 1.2)
                        )
                        .shadow(color: StudioTheme.cyanAccent.opacity(0.25), radius: 10)
                }

                VStack(alignment: .leading, spacing: 5) {
                    HStack(spacing: 8) {
                        Text("PHOENIX FORGE HARDWARE BENCH")
                            .font(.system(size: 14.5, weight: .heavy, design: .rounded))
                            .tracking(0.8)
                            .foregroundColor(.white)
                        Text("LIVE TELEMETRY")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(StudioTheme.cyanAccent.opacity(0.18)))
                            .foregroundColor(StudioTheme.cyanAccent)
                    }

                    Text("Native BootForge USB Descriptor Engine · Apple iOS/iPadOS & 20+ Android OEM Silicon Matrix")
                        .font(.system(size: 11.5))
                        .foregroundColor(.white.opacity(0.75))

                    HStack(spacing: 10) {
                        Label("\(engine.devices.count) Target\(engine.devices.count == 1 ? "" : "s")", systemImage: "cable.connector")
                            .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                            .foregroundColor(engine.devices.isEmpty ? StudioTheme.amberAccent : .green)
                        Text("·").foregroundColor(.secondary)
                        Label("Link: \(engine.connectionGrade)", systemImage: "waveform.path.ecg")
                            .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                            .foregroundColor(StudioTheme.cyanAccent)
                        Text("·").foregroundColor(.secondary)
                        Label("IOKit Hotplug Armed", systemImage: "bolt.shield.fill")
                            .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                            .foregroundColor(.white.opacity(0.78))
                    }
                }

                Spacer()
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
        }
        .frame(height: 112)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(
                    LinearGradient(colors: [StudioTheme.borderCyan, StudioTheme.amberAccent.opacity(0.22)], startPoint: .topLeading, endPoint: .bottomTrailing),
                    lineWidth: 1
                )
        )
    }
}

struct ConnectionMatrixAndDoctorView: View {
    @ObservedObject var engine: ServicingEngine

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            StudioWorkbenchHeroBanner(engine: engine)

            ModuleHeader(
                title: "BobFWTools Connection Matrix & USB Cable Doctor",
                subtitle: "Real-time BootForge USB descriptor enumeration, Device Intake Hub, 1/2/3-click autonomous workflows, and hardware diagnostics"
            )

            // High-Vibe Clean Shop Dashboard: Device Intake Hub (Conditional Connected vs. Line Empty UI + AES-GCM Encrypted History)
            DeviceIntakeHubCard(engine: engine)

            // Universal Multi-Platform Firmware & Carrier Match Card
            if let match = engine.universalMatch {
                GroupBox(label: Label("Universal Hardware & Firmware Auto-Matcher (\(match.platform.rawValue))", systemImage: match.platform.badgeIcon)) {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(match.targetName)
                                .font(.system(size: 13, weight: .bold))
                            Spacer()
                            Text(match.securityBitOrIosVer)
                                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(RoundedRectangle(cornerRadius: 4).fill(Color.green.opacity(0.18)))
                                .foregroundColor(.green)
                        }

                        HStack(spacing: 14) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("STOCK FIRMWARE TARGET:")
                                    .font(.system(size: 9.5, weight: .bold))
                                    .foregroundColor(.secondary)
                                Text(match.stockFirmwareBuild)
                                    .font(.system(size: 11.5, weight: .bold, design: .monospaced))
                                    .foregroundColor(.primary)
                            }
                            Divider().frame(height: 24)
                            VStack(alignment: .leading, spacing: 2) {
                                Text("COMBINATION / FACTORY TARGET:")
                                    .font(.system(size: 9.5, weight: .bold))
                                    .foregroundColor(.secondary)
                                Text(match.combinationFactoryBuild)
                                    .font(.system(size: 11.5, weight: .bold, design: .monospaced))
                                    .foregroundColor(.accentColor)
                            }
                            Divider().frame(height: 24)
                            VStack(alignment: .leading, spacing: 2) {
                                Text("CARRIER / CSC / REGION:")
                                    .font(.system(size: 9.5, weight: .bold))
                                    .foregroundColor(.secondary)
                                Text(match.carrierCscOrRegion)
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.secondary)
                            }
                        }

                        Text("Partition Table / PIT: \(match.partitionTableOrPit) · Match Status: \(match.isAntiRollbackSafe ? "Anti-Rollback Verified (Safe)" : "Review Required") [\(match.isFallbackSynthesized ? "Fallback Matrix Synthesized" : "Local Disk Mapped")]")
                            .font(.system(size: 10.5, design: .monospaced))
                            .foregroundColor(.secondary)

                        if !match.hardwareTestCode.isEmpty || match.fastbootdSupported || !match.controlCapabilities.isEmpty {
                            Divider()
                            HStack(spacing: 8) {
                                if !match.hardwareTestCode.isEmpty {
                                    HStack(spacing: 4) {
                                        Image(systemName: "number.circle.fill")
                                            .foregroundColor(.cyan)
                                        Text("DIAG: \(match.hardwareTestCode)")
                                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                                            .foregroundColor(.cyan)
                                    }
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(RoundedRectangle(cornerRadius: 4).fill(Color.cyan.opacity(0.12)))
                                }
                                if match.fastbootdSupported {
                                    HStack(spacing: 4) {
                                        Image(systemName: "cube.transparent.fill")
                                            .foregroundColor(.purple)
                                        Text("FASTBOOTD READY")
                                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                                            .foregroundColor(.purple)
                                    }
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(RoundedRectangle(cornerRadius: 4).fill(Color.purple.opacity(0.12)))
                                }
                                Spacer()
                            }
                        }
                    }
                    .padding(8)
                }
            }

            // Universal Multi-Brand Device Control Hub
            UniversalDeviceControlHubCard(engine: engine)

            // 1 / 2 / 3-Click Autonomous Workflows Card
            GroupBox(label: Label("1 / 2 / 3-Click Autonomous Diagnostic & Preflight Workflows", systemImage: "sparkles.rectangle.stack.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Execute multi-step BobFWTools diagnostic and preflight pipelines with a single click:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 10) {
                        Button {
                            Task { await engine.runAutonomousWorkflow(id: "quick-diagnostics") }
                        } label: {
                            Label("1-Click: Quick Mobile Diagnostics", systemImage: "1.circle.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(engine.isBusy)

                        Button {
                            Task { await engine.runAutonomousWorkflow(id: "vessel-sanctum") }
                        } label: {
                            Label("2-Click: VesselSanctum Deep Scan", systemImage: "2.circle.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(engine.isBusy)

                        Button {
                            Task { await engine.runAutonomousWorkflow(id: "partition-preflight") }
                        } label: {
                            Label("3-Click: Partition & Provisioning Preflight", systemImage: "3.circle.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(engine.isBusy)

                        Button {
                            Task { await engine.runCustomerIntakeClearance() }
                        } label: {
                            Label("4-Click: Customer Intake Clearance", systemImage: "checkmark.seal.text.page.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(engine.isBusy)
                    }

                    if let intake = engine.intakeClearanceReport {
                        Divider()
                        VStack(alignment: .leading, spacing: 5) {
                            HStack {
                                Text("PRE-REPAIR CUSTOMER INTAKE REPORT — \(intake.deviceModel) (SN: \(intake.serialNumber))")
                                    .font(.system(size: 12, weight: .bold))
                                Spacer()
                                Text(intake.clearanceStatus)
                                    .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 2)
                                    .background(RoundedRectangle(cornerRadius: 4).fill(Color.green.opacity(0.2)))
                                    .foregroundColor(.green)
                            }
                            Text("Carrier Lock: \(intake.carrierLockStatus) · Build/Bit: \(intake.bootloaderBit) · CSC: \(intake.regionCsc) · State: \(intake.runtimeState)")
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.secondary)
                            HStack(spacing: 12) {
                                ForEach(Array(intake.checklist.enumerated()), id: \.offset) { _, item in
                                    HStack(spacing: 4) {
                                        Image(systemName: item.1 ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                                            .foregroundColor(item.1 ? .green : .orange)
                                        Text("\(item.0): \(item.2)")
                                            .font(.system(size: 10.5))
                                    }
                                }
                            }
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 8).fill(Color(NSColor.controlBackgroundColor)))
                    }
                }
                .padding(8)
            }

            // Connection Matrix Card
            GroupBox(label: Label("Active Transport Connection Matrix (BootForge USB × Modem AT × ADB × Fastboot)", systemImage: "network")) {
                VStack(alignment: .leading, spacing: 10) {
                    if engine.matrixRows.isEmpty {
                        Text("No recognized mobile servicing device currently on the USB bus.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .padding(.vertical, 6)
                    } else {
                        ForEach(engine.matrixRows) { row in
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text(row.label)
                                        .font(.system(size: 14, weight: .bold))
                                    Spacer()
                                    Text("VID:PID \(row.vidPid) · SN: \(row.serial)")
                                        .font(.system(size: 11.5, design: .monospaced))
                                        .foregroundColor(.secondary)
                                }

                                HStack(spacing: 12) {
                                    TransportPill(title: "USB Descriptor", active: row.usbConnected, detail: "Connected")
                                    TransportPill(title: "Modem (AT)", active: row.modemPort != nil, detail: row.modemPort.map { ($0 as NSString).lastPathComponent } ?? "Unbound")
                                    TransportPill(title: "MTP Session", active: row.mtpActive, detail: row.mtpActive ? "Active" : "Inactive")
                                    TransportPill(title: "ADB", active: row.adbState == "device", detail: row.adbState)
                                    TransportPill(title: "Odin / Fastboot", active: row.odinActive || row.fastbootActive, detail: row.odinActive ? "Download" : (row.fastbootActive ? "Fastboot" : "Standby"))
                                }

                                Text("Platform: \(row.platformClassification) · Evidence: \(row.evidence.joined(separator: " + "))")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.secondary)
                            }
                            .padding(10)
                            .background(RoundedRectangle(cornerRadius: 8).fill(Color(NSColor.controlBackgroundColor)))
                        }
                    }

                    HStack(spacing: 10) {
                        Button("Inspect USB Descriptors (bootforgeusb scan)") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "bootforge.endpoints",
                                    title: "BootForge USB Endpoint Enumeration",
                                    executable: engine.bootforgeBinaryPath,
                                    arguments: ["scan"]
                                )
                            }
                        }
                        Button("Probe Samsung Modem Identity (AT+DEVCONINFO)") {
                            Task {
                                await engine.sendATCommand(portPath: engine.selectedSerialPort, command: "AT+DEVCONINFO")
                            }
                        }
                        Button("Run USB Cable Doctor (5x Stability Test)") {
                            Task { await engine.runUsbCableDoctor() }
                        }
                    }
                }
                .padding(8)
            }

            // USB Cable Doctor Report Card
            if let doc = engine.cableDoctorReport {
                GroupBox(label: Label("USB Cable Doctor Report — Grade: \(doc.grade)", systemImage: "waveform.path.ecg")) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(doc.summary)
                            .font(.system(size: 12.5, weight: .semibold))
                        Text("Samples: \(doc.presentSamples)/\(doc.samples) · Reconnect Drops: \(doc.reconnectEvents) · Speeds: \(doc.observedSpeeds.joined(separator: ", ")) · Modem Port: \(doc.modemPortPresent ? "Present" : "None")")
                            .font(.system(size: 11.5, design: .monospaced))
                            .foregroundColor(.secondary)
                        ForEach(doc.recommendations, id: \.self) { rec in
                            Text("• \(rec)")
                                .font(.caption)
                        }
                    }
                    .padding(8)
                }
            }

            // BobFWTools Diagnostic Findings
            GroupBox(label: Label("BobFWTools Automated Diagnostic Findings", systemImage: "checklist")) {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(engine.diagnosticFindings) { f in
                        HStack(alignment: .top, spacing: 8) {
                            Text(f.severity)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(RoundedRectangle(cornerRadius: 4).fill(severityColor(f.severity).opacity(0.2)))
                                .foregroundColor(severityColor(f.severity))

                            VStack(alignment: .leading, spacing: 2) {
                                Text(f.title)
                                    .font(.system(size: 12, weight: .semibold))
                                Text(f.detail)
                                    .font(.system(size: 11.5))
                                    .foregroundColor(.secondary)
                                if let rec = f.recommendation {
                                    Text("Recommendation: \(rec)")
                                        .font(.system(size: 11))
                                        .foregroundColor(.accentColor)
                                }
                            }
                        }
                    }
                }
                .padding(8)
            }
        }
    }

    private func severityColor(_ s: String) -> Color {
        switch s {
        case "OK": return .green
        case "WARN": return .orange
        default: return .red
        }
    }
}

struct TransportPill: View {
    let title: String
    let active: Bool
    let detail: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 4) {
                Circle()
                    .fill(active ? Color.green : Color.secondary.opacity(0.5))
                    .frame(width: 6, height: 6)
                Text(title)
                    .font(.system(size: 10, weight: .bold))
            }
            Text(detail)
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(.secondary)
                .lineLimit(1)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 5)
        .background(RoundedRectangle(cornerRadius: 6).stroke(active ? Color.green.opacity(0.5) : Color.secondary.opacity(0.2), lineWidth: 1))
    }
}

// MARK: - High-Vibe Clean Shop Dashboard: Device Intake Hub + AES-GCM Encrypted Customer Intake History

struct DeviceIntakeHubCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var customerLabelInput: String = ""

    private var isConnected: Bool {
        engine.samsungModemInfo != nil || !engine.devices.isEmpty || !engine.serialPorts.isEmpty
    }

    private var modelName: String {
        if let info = engine.samsungModemInfo, !info.model.isEmpty {
            return info.model
        }
        if let row = engine.matrixRows.first {
            return row.model
        }
        return engine.selectedDevice?.name ?? "Unknown Target"
    }

    private var securityBitNumber: Int {
        if let report = engine.intakeClearanceReport, report.securityBit > 0 {
            return report.securityBit
        }
        if let info = engine.samsungModemInfo {
            let parsed = DiagnosticParser.extractClearanceData(from: info.rawResponse, fallbackModem: info)
            if parsed.securityBit > 0 { return parsed.securityBit }
        }
        return engine.autoMatchedBundle?.bootloaderBit ?? 8
    }

    private var serialNumberText: String {
        if let info = engine.samsungModemInfo, !info.serialNumber.isEmpty {
            return info.serialNumber
        }
        if let row = engine.matrixRows.first, !row.serial.isEmpty {
            return row.serial
        }
        if let devSerial = engine.selectedDevice?.serial, !devSerial.isEmpty {
            return devSerial
        }
        return "Awaiting Device Link"
    }

    private var regionCodeText: String {
        if let info = engine.samsungModemInfo, !info.activeCsc.isEmpty {
            return info.activeCsc
        }
        if let report = engine.intakeClearanceReport, !report.regionCsc.isEmpty {
            return report.regionCsc
        }
        if let csc = engine.autoMatchedBundle?.cscContainerVersion, !csc.isEmpty {
            return csc
        }
        return "N/A"
    }

    private var clearanceBadgeText: String {
        if let report = engine.intakeClearanceReport {
            return report.clearanceStatus
        }
        if let info = engine.samsungModemInfo {
            let parsed = DiagnosticParser.extractClearanceData(from: info.rawResponse, fallbackModem: info)
            return parsed.antiRollbackStatus
        }
        return engine.devices.isEmpty ? "NO TARGET CONNECTED" : "AWAITING CLEARANCE"
    }

    private var isClearedForService: Bool {
        clearanceBadgeText.contains("CLEARED")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Header Row: Device Intake Hub + Live Connection Badge
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Device Intake Hub")
                        .font(.system(size: 16, weight: .semibold))
                    Text("Automatic USB / Serial AT telemetry with disconnect state clearing & AES-GCM hardware-bound intake logging")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
                Spacer()
                HStack(spacing: 6) {
                    Circle()
                        .fill(isConnected ? Color.green : Color.secondary)
                        .frame(width: 8, height: 8)
                    Text(isConnected ? "Device Live" : "Waiting for USB")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(isConnected ? .green : .secondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 5)
                .background(
                    Capsule()
                        .fill(isConnected ? Color.green.opacity(0.14) : Color.secondary.opacity(0.12))
                )
            }

            // Conditional Rendering: Active Device Telemetry vs. Clean "Line Empty" Slot
            if isConnected {
                VStack(alignment: .leading, spacing: 12) {
                    // 2-Column Grid: Device Model & Security Revision
                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("DEVICE MODEL")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                            Text(modelName)
                                .font(.system(size: 17, weight: .bold, design: .monospaced))
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(12)
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color(NSColor.windowBackgroundColor)))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.secondary.opacity(0.15), lineWidth: 1))

                        VStack(alignment: .leading, spacing: 4) {
                            Text("SECURITY REVISION")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                            Text("Binary \(securityBitNumber)")
                                .font(.system(size: 17, weight: .bold, design: .monospaced))
                                .foregroundColor(.blue)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(12)
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color(NSColor.windowBackgroundColor)))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.secondary.opacity(0.15), lineWidth: 1))
                    }

                    // Serial Identifier + Region Badge Row
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("SERIAL IDENTIFIER")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                            Text(serialNumberText)
                                .font(.system(size: 13.5, weight: .semibold, design: .monospaced))
                        }
                        Spacer()
                        Text("Region: \(regionCodeText)")
                            .font(.system(size: 11.5, weight: .semibold, design: .monospaced))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(RoundedRectangle(cornerRadius: 6).fill(Color.secondary.opacity(0.14)))
                    }
                    .padding(12)
                    .background(RoundedRectangle(cornerRadius: 10).fill(Color(NSColor.windowBackgroundColor)))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.secondary.opacity(0.15), lineWidth: 1))

                    // System Authorization Banner
                    HStack {
                        Text("SYSTEM AUTHORIZATION")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(isClearedForService ? .green : .orange)
                        Spacer()
                        Text(clearanceBadgeText)
                            .font(.system(size: 12, weight: .bold, design: .monospaced))
                            .foregroundColor(isClearedForService ? .green : .orange)
                    }
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 10)
                            .fill((isClearedForService ? Color.green : Color.orange).opacity(0.10))
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke((isClearedForService ? Color.green : Color.orange).opacity(0.30), lineWidth: 1)
                    )

                    // Cryptographic Customer Intake Logger Bar (HardwareLogProtector AES-GCM + HKDF<SHA256>)
                    HStack(spacing: 10) {
                        TextField("Customer / Ticket Label (e.g. Walk-In #104 — Galaxy Tab A7 EUX)...", text: $customerLabelInput)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11.5))

                        Button {
                            Task {
                                if engine.intakeClearanceReport == nil {
                                    await engine.runCustomerIntakeClearance()
                                }
                                engine.encryptAndRecordCustomerIntake(customerLabel: customerLabelInput)
                                customerLabelInput = ""
                            }
                        } label: {
                            Label("Encrypt & Seal Intake Log (AES-GCM)", systemImage: "lock.doc.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(engine.isBusy)

                        Button {
                            engine.clearTelemetryOnDisconnect()
                        } label: {
                            Label("Clear Bench Slot", systemImage: "xmark.circle")
                        }
                        .help("Manually clear the active workbench telemetry slot")
                    }
                }
            } else {
                // Clean Dashed Empty Slot when unplugged
                VStack(spacing: 8) {
                    Image(systemName: "cable.connector.horizontal")
                        .font(.system(size: 24))
                        .foregroundColor(.secondary)
                    Text("Line Empty")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.secondary)
                    Text("Connect a target device to initialize service — telemetry populates automatically on USB / AT handshake")
                        .font(.system(size: 11.5))
                        .foregroundColor(.secondary.opacity(0.8))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 32)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .strokeBorder(style: StrokeStyle(lineWidth: 2, dash: [6, 5]))
                        .foregroundColor(Color.secondary.opacity(0.25))
                )
            }

            // Servicing History Ledger Browser (Per-Customer JSONL records/cust_*.db + Instant Search & Filter Bar)
            Divider()
            ServicingHistoryLedgerCard(engine: engine)

            // Persistent Customer Intake History Database (AES-GCM Sealed Logs)
            if !engine.encryptedIntakeHistory.isEmpty {
                Divider()
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Label("Customer Intake History Database (HardwareLogProtector AES-GCM + HKDF-SHA256)", systemImage: "externaldrive.badge.checkmark")
                            .font(.system(size: 11.5, weight: .bold))
                        Spacer()
                        if !engine.decryptedLogPreview.isEmpty {
                            Text(engine.decryptedLogPreview)
                                .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                                .foregroundColor(.green)
                                .lineLimit(1)
                        }
                    }

                    ForEach(engine.encryptedIntakeHistory.prefix(5)) { rec in
                        HStack(spacing: 10) {
                            Image(systemName: "lock.shield.fill")
                                .foregroundColor(.green)
                            Text(rec.customerLabel)
                                .font(.system(size: 11, weight: .semibold))
                            Text("\(rec.model) · Bin \(rec.securityBit) · \(rec.rawSwRev) · SN: \(rec.deviceIdentifier)")
                                .font(.system(size: 10.5, design: .monospaced))
                                .foregroundColor(.secondary)
                            Spacer()
                            Text(rec.status)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundColor(rec.status.contains("CLEARED") ? .green : .orange)
                            Button("Verify AES-GCM") {
                                engine.verifyAndDecryptIntakeRecord(rec)
                            }
                            .controlSize(.mini)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.windowBackgroundColor)))
                    }
                }
            }
        }
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 14).fill(Color(NSColor.controlBackgroundColor)))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.secondary.opacity(0.18), lineWidth: 1))
    }
}

struct ServicingHistoryLedgerCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var searchQuery: String = ""
    @State private var statusFilter: String = "ALL" // ALL, CLEARED, HOLD

    private var filteredRecords: [(IntakeLedgerRecord, DecodedTelemetryPayload)] {
        let query = searchQuery.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        var results: [(IntakeLedgerRecord, DecodedTelemetryPayload)] = []

        for rec in engine.servicingHistoryLedger {
            guard let telemetry = rec.decodeTelemetry() else { continue }

            // Status filter pill check
            if statusFilter == "CLEARED" && !telemetry.status.uppercased().contains("CLEARED") {
                continue
            }
            if statusFilter == "HOLD" && telemetry.status.uppercased().contains("CLEARED") {
                continue
            }

            // Instant search query check across Serial Number (SN), Device Model, Binary Version, CSC, or Customer ID
            if !query.isEmpty {
                let searchable = [
                    telemetry.serial_number,
                    telemetry.model,
                    "b\(telemetry.binary_version)",
                    telemetry.binary_version,
                    telemetry.carrier_csc,
                    telemetry.status,
                    rec.customer_id
                ].joined(separator: " ").lowercased()

                if !searchable.contains(query) {
                    continue
                }
            }
            results.append((rec, telemetry))
        }
        return results
    }

    private func formatDate(_ ts: UInt64) -> String {
        let date = Date(timeIntervalSince1970: TimeInterval(ts))
        let fmt = DateFormatter()
        fmt.dateStyle = .short
        fmt.timeStyle = .short
        return fmt.string(from: date)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header Row: Servicing History Ledger + Auto-Commit Toggle + Refresh Index
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Servicing History Ledger")
                        .font(.system(size: 13.5, weight: .bold))
                    Text("Stored local checkpoint snapshots (records/cust_\(engine.activeCustomerId).db) · Auto-commits on live device scan")
                        .font(.system(size: 10.5))
                        .foregroundColor(.secondary)
                }
                Spacer()

                Toggle("Auto-Commit on Scan", isOn: $engine.autoCommitIntakeOnScan)
                    .toggleStyle(.checkbox)
                    .font(.system(size: 11))

                Button {
                    engine.autoCommitCurrentTelemetryToLedger(force: true)
                } label: {
                    Label("Commit Snapshot", systemImage: "plus.rectangle.on.folder.fill")
                }
                .controlSize(.small)

                Button {
                    engine.fetchCustomerHistory(customerId: "ALL")
                } label: {
                    Label("Refresh Index", systemImage: "arrow.clockwise")
                }
                .controlSize(.small)
            }

            // Instant Search & Filter Bar (by Serial Number, Device Model, Binary Version, or Customer ID)
            HStack(spacing: 8) {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.secondary)
                        .font(.system(size: 11.5))
                    TextField("Search ledger by Serial Number, Model, Binary Bit, CSC, or Customer ID...", text: $searchQuery)
                        .textFieldStyle(.plain)
                        .font(.system(size: 11.5, design: .monospaced))
                    if !searchQuery.isEmpty {
                        Button {
                            searchQuery = ""
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(RoundedRectangle(cornerRadius: 8).fill(Color(NSColor.windowBackgroundColor)))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.secondary.opacity(0.22), lineWidth: 1))

                HStack(spacing: 6) {
                    Text("Customer ID:")
                        .font(.system(size: 10.5, weight: .semibold))
                        .foregroundColor(.secondary)
                    TextField("WALK_IN_DEFAULT", text: $engine.activeCustomerId)
                        .textFieldStyle(.roundedBorder)
                        .font(.system(size: 11, design: .monospaced))
                        .frame(width: 145)
                }

                Picker("", selection: $statusFilter) {
                    Text("All (\(engine.servicingHistoryLedger.count))").tag("ALL")
                    Text("Cleared").tag("CLEARED")
                    Text("Hold").tag("HOLD")
                }
                .pickerStyle(.segmented)
                .frame(width: 195)
            }

            // Ledger Rows
            if filteredRecords.isEmpty {
                Text(searchQuery.isEmpty ? "No historical clearance signatures found." : "No history records match '\(searchQuery)'.")
                    .font(.system(size: 11.5))
                    .foregroundColor(.secondary)
                    .italic()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 14)
            } else {
                ScrollView {
                    VStack(spacing: 6) {
                        ForEach(filteredRecords, id: \.0.id) { record, telemetry in
                            let isCleared = telemetry.status.uppercased().contains("CLEARED")
                            HStack {
                                VStack(alignment: .leading, spacing: 3) {
                                    HStack(spacing: 8) {
                                        Text(telemetry.model)
                                            .font(.system(size: 12, weight: .semibold))
                                        Text("B\(telemetry.binary_version)")
                                            .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 1)
                                            .background(RoundedRectangle(cornerRadius: 4).fill(Color.blue.opacity(0.15)))
                                            .foregroundColor(.blue)
                                        if !telemetry.carrier_csc.isEmpty {
                                            Text("CSC: \(telemetry.carrier_csc)")
                                                .font(.system(size: 10.5, design: .monospaced))
                                                .foregroundColor(.secondary)
                                        }
                                        Text("cust_\(record.customer_id).db")
                                            .font(.system(size: 10, design: .monospaced))
                                            .foregroundColor(.secondary.opacity(0.8))
                                    }
                                    Text("SN: \(telemetry.serial_number)")
                                        .font(.system(size: 10.5, design: .monospaced))
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                                VStack(alignment: .trailing, spacing: 3) {
                                    Text(isCleared ? "CLEARED" : "HOLD")
                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 2)
                                        .background(
                                            RoundedRectangle(cornerRadius: 4)
                                                .fill((isCleared ? Color.green : Color.orange).opacity(0.14))
                                        )
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 4)
                                                .stroke((isCleared ? Color.green : Color.orange).opacity(0.35), lineWidth: 1)
                                        )
                                        .foregroundColor(isCleared ? .green : .orange)

                                    Text(formatDate(record.timestamp))
                                        .font(.system(size: 9.5, design: .monospaced))
                                        .foregroundColor(.secondary)
                                }
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(RoundedRectangle(cornerRadius: 9).fill(Color(NSColor.windowBackgroundColor)))
                            .overlay(RoundedRectangle(cornerRadius: 9).stroke(Color.secondary.opacity(0.15), lineWidth: 1))
                        }
                    }
                }
                .frame(maxHeight: 190)
            }
        }
    }
}

// MARK: - Module 1B: Owner Pro Vault (A12+ iDevices, Flagship Samsung S/Z/A/Tab, MediaTek & Unisoc SPD — Zero Paywall)

struct OwnerProVaultView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var licenseKeyInput: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                ModuleHeader(
                    title: "Owner Pro Vault — A12+ iOS, Galaxy S/Z/A/Tab, MediaTek & Unisoc (SPD)",
                    subtitle: engine.isProUnlocked
                        ? "Full unlocked owner build — zero paywalls, zero credit gates, and full local hardware coverage"
                        : "Store Edition Preview — Free tier diagnostics are active; Pro Vault modules require BobFWTools Pro activation"
                )
                Spacer()
                Label(engine.isProUnlocked ? "ALL PRO MODULES UNLOCKED" : "STORE PAYWALL ACTIVE", systemImage: engine.isProUnlocked ? "lock.open.fill" : "lock.fill")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(RoundedRectangle(cornerRadius: 8).fill((engine.isProUnlocked ? Color.green : Color.orange).opacity(0.18)))
                    .foregroundColor(engine.isProUnlocked ? .green : .orange)
            }

            GroupBox(label: Label("Asymmetric Ed25519 License & Edition Verification (CryptoKit Curve25519)", systemImage: "key.horizontal.fill")) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Verification Status: \(engine.licenseStatusSummary)")
                            .font(.system(size: 11.5, weight: .semibold, design: .monospaced))
                            .foregroundColor(engine.isProUnlocked ? .green : .orange)
                        Spacer()
                        #if !STORE_EDITION
                        Button("Mint & Sign Ed25519 Customer Token") {
                            let token = CryptographicLicenseVerifier.generateSignedToken(holder: "Authorized Pro Shop")
                            licenseKeyInput = token
                            _ = engine.verifyAndActivateLicenseToken(token)
                        }
                        .controlSize(.small)
                        #endif
                    }

                    HStack(spacing: 10) {
                        TextField("Signed BOBFW.<payload>.<ed25519_sig> token...", text: $licenseKeyInput)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11.5, design: .monospaced))

                        Button("Verify Ed25519 Token") {
                            _ = engine.verifyAndActivateLicenseToken(licenseKeyInput)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding(8)
            }
            .onAppear {
                if licenseKeyInput.isEmpty {
                    licenseKeyInput = engine.signedLicenseToken
                }
            }

            // Section 1: Apple A12+ (iPhone XS -> 16 Pro Max / M1-M4 iPad) Pro Telemetry & Recovery Vault
            GroupBox(label: Label("Apple A12+ – A18 Pro & M-Series Pro Telemetry, Activation & IPSW Suite (Unlocked)", systemImage: "iphone.badge.play")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text("Supports A10–A18 Pro (CPID 0x8010–0x8140) and M1–M4 Apple Silicon:")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("USB Mode: \(engine.appleModeStatusBadge)")
                            .font(.caption.bold().monospaced())
                            .foregroundColor(engine.appleModeStatusBadge.contains("RESTORE") ? .cyan : (engine.appleModeStatusBadge.contains("RECOVERY") ? .orange : (engine.appleModeStatusBadge.contains("NORMAL") ? .green : .secondary)))
                    }

                    HStack(spacing: 8) {
                        Button {
                            Task { await engine.runAppleA12ProAudit() }
                        } label: {
                            Label("Run Apple Mode & Silicon Audit", systemImage: "cpu.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.purple)

                        Button {
                            Task { await engine.exitAppleRecoveryMode() }
                        } label: {
                            Label("Exit Recovery Mode (irecovery -n)", systemImage: "arrow.uturn.backward.circle.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.green)

                        Button {
                            Task { await engine.forceAutoBootTrueAndReboot() }
                        } label: {
                            Label("Force Auto-Boot True & Reboot", systemImage: "bolt.fill")
                        }
                        .buttonStyle(.bordered)

                        Button {
                            Task { await engine.querySignedIpswCatalogOnline() }
                        } label: {
                            Label("Find Signed IPSW (Apple TSS)", systemImage: "arrow.down.doc.fill")
                        }
                        .buttonStyle(.bordered)
                        .tint(.blue)
                    }

                    HStack(spacing: 8) {
                        Button {
                            if let path = pickFile(allowedExtensions: ["ipsw"]) {
                                Task { await engine.restoreAppleDeviceWithIpsw(path: path, keepData: false) }
                            }
                        } label: {
                            Label("1-Click IPSW Restore...", systemImage: "play.circle.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.indigo)

                        Button("Read DFU / Recovery (irecovery -q)") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "pro.apple_irecovery",
                                    title: "Read iBoot / DFU Identity",
                                    executable: engine.toolPaths["irecovery"]!,
                                    arguments: ["-q"]
                                )
                            }
                        }

                        Button("Reboot Target") {
                            Task { await engine.rebootAppleRestoreDevice() }
                        }

                        Button("Check MDM / Supervision") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "pro.apple_mdm_check",
                                    title: "Query iOS Supervision & Cloud Configuration",
                                    executable: engine.toolPaths["ideviceinfo"]!,
                                    arguments: ["-q", "com.apple.mobile.chaperone"]
                                )
                            }
                        }

                        Button("Physical DFU Guide") {
                            engine.showAppleDfuGuide()
                        }

                        Button {
                            engine.exportCustomerRepairReceipt()
                        } label: {
                            Label("Intake Certificate", systemImage: "doc.badge.arrow.up.fill")
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding(8)
            }

            // Section 2: Flagship Samsung S / Z / A / Tab Pro Security & Knox Suite
            GroupBox(label: Label("Flagship Samsung Galaxy S / Z Fold / Flip / A / Tab Pro Suite (Unlocked)", systemImage: "shield.lefthalf.filled.badge.checkmark")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Covers Galaxy S20–S25 Ultra, Z Fold/Flip 3–6, Galaxy A03–A55/A73, and Galaxy Tab S / Tab A series:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 10) {
                        Button {
                            Task { await engine.runSamsungProSecurityAudit() }
                        } label: {
                            Label("Run Knox Guard (KG) / Warranty / Bootloader Audit", systemImage: "checkmark.shield.fill")
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Auto-Match Local Firmware & Optics CSCs") {
                            Task { await engine.autoDiscoverAndMatchBinaries() }
                        }

                        Button("Read Modem EFS / NV & Carrier Lock (AT+DEVCONINFO)") {
                            Task { await engine.sendATCommand(portPath: engine.selectedSerialPort, command: "AT+DEVCONINFO") }
                        }
                    }
                }
                .padding(8)
            }

            // Section 3: MediaTek (MTK) & Unisoc / Spreadtrum (SPD) Chipset Studio
            GroupBox(label: Label("MediaTek (MTK BROM/Preloader) & Unisoc / Spreadtrum (SPD Diag/FDL) Chipset Studio (Unlocked)", systemImage: "memorychip.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Native USB VID:PID detection for MediaTek (0e8d:0003 BROM, 0e8d:2000 Preloader) and Unisoc/SPD (1782:4d00 Diag/FDL, 1782:4d03) plus Scatter & .PAC inspection:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 10) {
                        Button {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "pro.mtk_spd_scan",
                                    title: "Scan USB Bus for MTK (0e8d) & Unisoc SPD (1782) Interfaces",
                                    executable: engine.bootforgeBinaryPath,
                                    arguments: ["scan"]
                                )
                            }
                        } label: {
                            Label("Scan MTK / SPD / EDL Interfaces", systemImage: "cable.connector.horizontal")
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Inspect MediaTek Scatter (MT*_scatter.txt)...") {
                            if let path = pickFile(allowedExtensions: ["txt", "xml"]) {
                                Task { await engine.inspectMtkOrSpdPackage(path: path) }
                            }
                        }

                        Button("Inspect Unisoc .PAC / FDL1 / FDL2 Binary...") {
                            if let path = pickFile(allowedExtensions: ["pac", "bin", "img", "sign"]) {
                                Task { await engine.inspectMtkOrSpdPackage(path: path) }
                            }
                        }
                    }
                }
                .padding(8)
            }

            // Section 3.5: Phoenix Sanctum — Root Privilege, Silicon Fuse & Hash-Chained Shadow Ledger
            GroupBox(label: Label("Phoenix Sanctum — Root Privilege, Silicon Fuse & Hash-Chained Shadow Ledger", systemImage: "lock.trianglebadge.exclamationmark.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Live privilege vector detection (Magisk / KernelSU / APatch / SELinux / AVB vbmeta), silicon fuse posture, and SHA-256 tamper-evident hash chain:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 12) {
                        Button {
                            Task { await engine.runPhoenixSanctumRootAndSiliconAudit() }
                        } label: {
                            Label("Run Phoenix Sanctum Privilege & Silicon Audit", systemImage: "cpu.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.purple)

                        Button {
                            Task { await engine.runPhoenixSanctumSiliconProbe() }
                        } label: {
                            Label("Live Probe EDL 9008 / MTK BROM", systemImage: "bolt.horizontal.circle.fill")
                        }
                        .buttonStyle(.bordered)

                        Button {
                            Task { await engine.runPhoenixSanctumEfsBackup() }
                        } label: {
                            Label("Backup EFS / NVRAM to Sanctum Vault", systemImage: "externaldrive.fill.badge.checkmark")
                        }
                        .buttonStyle(.bordered)

                        VStack(alignment: .leading, spacing: 2) {
                            Text("Shadow Chain Entries: \(engine.sanctumChainCount)")
                                .font(.caption.monospaced())
                            Text("Chain Head SHA-256: \(String(engine.sanctumChainHeadHash.prefix(24)))...")
                                .font(.caption2.monospaced())
                                .foregroundColor(.secondary)
                        }
                    }

                    Text(engine.sanctumPrivilegeSummary)
                        .font(.system(.caption, design: .monospaced))
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.black.opacity(0.25))
                        .cornerRadius(6)
                }
                .padding(8)
            }

            // Section 4: Master Supported Hardware & Chipset Coverage Matrix
            GroupBox(label: Label("Master Hardware & Chipset Coverage Matrix (\(engine.platformCatalog.count) Device & SoC Families)", systemImage: "list.bullet.rectangle.portrait.fill")) {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(engine.platformCatalog) { item in
                        VStack(alignment: .leading, spacing: 3) {
                            HStack {
                                Text(item.family)
                                    .font(.system(size: 12.5, weight: .bold))
                                Spacer()
                                Text("USB \(item.usbVidPid) · \(item.protocolName)")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.accentColor)
                            }
                            Text("Models / SoCs: \(item.modelsOrChips)")
                                .font(.system(size: 11.5))
                                .foregroundColor(.secondary)
                            Text("Operations: \(item.supportedOperations)")
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.primary)
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                    }
                }
                .padding(8)
            }
            .disabled(!engine.isProUnlocked)
            .opacity(engine.isProUnlocked ? 1.0 : 0.55)
        }
    }
}

// MARK: - Module 2: BobFWTools Samsung Servicing & Odin Planner

struct SamsungCloudFirmwareHubCard: View {
    @ObservedObject var engine: ServicingEngine

    var body: some View {
        GroupBox(label: Label("Autonomous 1-Click Samsung Cloud Firmware & Odin Flasher", systemImage: "bolt.shield.fill")) {
            VStack(alignment: .leading, spacing: 14) {
                // Header & Hardware Identity
                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 3) {
                        HStack(spacing: 6) {
                            Text(targetModelTitle)
                                .font(.system(size: 13, weight: .bold))
                            Text(deviceModeBadge)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 1)
                                .background(RoundedRectangle(cornerRadius: 4).fill(Color.blue.opacity(0.18)))
                                .foregroundColor(.blue)
                        }
                        Text("Serial: \(targetSerial) · Current Binary: \(targetPda) · \(targetBit)")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Button {
                        Task { await engine.querySamsungCloudFirmwares() }
                    } label: {
                        if engine.isFirmwareQuerying {
                            ProgressView()
                                .controlSize(.small)
                                .padding(.trailing, 2)
                        }
                        Label("Auto-Detect & Query Cloud Firmwares", systemImage: "arrow.triangle.2.circlepath")
                    }
                    .buttonStyle(.bordered)
                    .disabled(engine.isFirmwareQuerying || engine.isFirmwareDownloading || engine.isFirmwareFlashing)
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 8).fill(Color.accentColor.opacity(0.06)))

                // Firmware Recommendations & Selection Panel
                if engine.samsungCloudFirmwares.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("No cloud firmwares queried yet.")
                            .font(.system(size: 11.5, weight: .semibold))
                            .foregroundColor(.secondary)
                        Text("Click 'Auto-Detect & Query Cloud Firmwares' to search Samsung Official FUS servers across all compatible carriers (TFN, VZW, XAA, etc.) and check local downloads.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                    .padding(8)
                } else {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Official Stock Firmware Candidates (User Selectable — Recommended Pre-Selected):")
                                .font(.system(size: 11.5, weight: .bold))
                            Spacer()
                            Text("\(engine.samsungCloudFirmwares.count) options found")
                                .font(.system(size: 10.5, design: .monospaced))
                                .foregroundColor(.secondary)
                        }

                        ScrollView(.vertical, showsIndicators: true) {
                            VStack(spacing: 8) {
                                ForEach(engine.samsungCloudFirmwares) { cand in
                                    let isSelected = engine.selectedCloudFirmware?.id == cand.id
                                    Button {
                                        engine.selectedCloudFirmware = cand
                                    } label: {
                                        HStack(alignment: .top, spacing: 10) {
                                            Image(systemName: isSelected ? "largecircle.fill.circle" : "circle")
                                                .font(.system(size: 14))
                                                .foregroundColor(isSelected ? .accentColor : .secondary)
                                                .padding(.top, 2)

                                            VStack(alignment: .leading, spacing: 4) {
                                                HStack(spacing: 8) {
                                                    Text(cand.pda)
                                                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                                                        .foregroundColor(.primary)

                                                    Text(cand.region)
                                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                                        .padding(.horizontal, 5)
                                                        .padding(.vertical, 1)
                                                        .background(RoundedRectangle(cornerRadius: 3).fill(Color.orange.opacity(0.18)))
                                                        .foregroundColor(.orange)

                                                    if cand.isRecommended {
                                                        Text("★ RECOMMENDED (Bit U:1 Safe)")
                                                            .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                                            .padding(.horizontal, 6)
                                                            .padding(.vertical, 1)
                                                            .background(RoundedRectangle(cornerRadius: 3).fill(Color.green.opacity(0.2)))
                                                            .foregroundColor(.green)
                                                    }

                                                    Spacer()

                                                    if cand.localFilesExist {
                                                        Label("Verified on Mac", systemImage: "checkmark.seal.fill")
                                                            .font(.system(size: 10, weight: .bold))
                                                            .foregroundColor(.green)
                                                    } else {
                                                        Label("Samsung Cloud (~6.4 GB)", systemImage: "icloud.and.arrow.down")
                                                            .font(.system(size: 10))
                                                            .foregroundColor(.secondary)
                                                    }
                                                }

                                                Text("\(cand.regionLabel) · CSC: \(cand.csc) · Target: \(cand.androidTarget)")
                                                    .font(.system(size: 11))
                                                    .foregroundColor(.secondary)

                                                if cand.localFilesExist {
                                                    Text("Location: \(cand.localFolderPath)")
                                                        .font(.system(size: 9.5, design: .monospaced))
                                                        .foregroundColor(.secondary.opacity(0.8))
                                                        .lineLimit(1)
                                                }
                                            }
                                        }
                                        .padding(10)
                                        .background(
                                            RoundedRectangle(cornerRadius: 8)
                                                .fill(isSelected ? Color.accentColor.opacity(0.08) : Color(NSColor.controlBackgroundColor))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 8)
                                                        .stroke(isSelected ? Color.accentColor : Color.secondary.opacity(0.2), lineWidth: isSelected ? 1.5 : 1)
                                                )
                                        )
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                            .padding(.vertical, 2)
                        }
                        .frame(maxHeight: 220)
                    }
                }

                Divider()

                // 1-Click Action & Live Progress
                if let selected = engine.selectedCloudFirmware {
                    VStack(alignment: .leading, spacing: 10) {
                        // Data-Preserving Bootloop Recovery & Baseband EFS Guard
                        HStack(spacing: 14) {
                            Toggle(isOn: $engine.preserveUserDataBootloopFix) {
                                VStack(alignment: .leading, spacing: 2) {
                                    HStack(spacing: 6) {
                                        Text("Non-Destructive Bootloop Recovery (HOME_CSC)")
                                            .font(.system(size: 11, weight: .bold))
                                        Text(engine.preserveUserDataBootloopFix ? "PRESERVE 100% PHOTOS & APPS" : "FACTORY DATA WIPE (CSC)")
                                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 5)
                                            .padding(.vertical, 1)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(engine.preserveUserDataBootloopFix ? Color.green.opacity(0.2) : Color.red.opacity(0.2)))
                                            .foregroundColor(engine.preserveUserDataBootloopFix ? .green : .red)
                                    }
                                    Text(engine.preserveUserDataBootloopFix ? "Reinstalls corrupted system partitions without touching user pictures, contacts, or apps." : "Full factory clean install: wipes all userdata and re-partitions device.")
                                        .font(.system(size: 10))
                                        .foregroundColor(.secondary)
                                }
                            }
                            .toggleStyle(.checkbox)

                            Spacer()

                            Button {
                                Task { _ = await engine.backupSamsungEfsAndCalibration() }
                            } label: {
                                Label("🛡️ EFS & Radio Snapshot", systemImage: "shield.lefthalf.filled")
                                    .font(.system(size: 10.5, weight: .semibold))
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.primary.opacity(0.03)))

                        HStack(spacing: 12) {
                            Button {
                                Task { await engine.downloadAndFlashSelectedSamsungFirmware(candidate: selected) }
                            } label: {
                                if engine.isFirmwareDownloading || engine.isFirmwareFlashing {
                                    ProgressView()
                                        .controlSize(.small)
                                        .padding(.trailing, 4)
                                }
                                Label(
                                    selected.localFilesExist ? "⚡ 1-Click Flash to Device (\(selected.pda))" : "⚡ 1-Click Download & Flash to Device (\(selected.pda))",
                                    systemImage: selected.localFilesExist ? "flame.fill" : "arrow.down.circle.fill"
                                )
                                .font(.system(size: 12, weight: .bold))
                                .padding(.vertical, 4)
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(selected.localFilesExist ? .green : .blue)
                            .disabled(engine.isFirmwareDownloading || engine.isFirmwareFlashing)

                            Button {
                                Task { _ = await engine.exitSamsungDownloadMode() }
                            } label: {
                                if engine.isExitingDownloadMode {
                                    ProgressView().controlSize(.small).padding(.trailing, 2)
                                }
                                Label("Exit Download Mode (Reboot)", systemImage: "arrow.uturn.backward.circle.fill")
                                    .font(.system(size: 11, weight: .semibold))
                            }
                            .buttonStyle(.bordered)
                            .tint(.orange)
                            .disabled(engine.isExitingDownloadMode || engine.isFirmwareFlashing)

                            if !engine.firmwareOperationStep.isEmpty {
                                Text(engine.firmwareOperationStep)
                                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                    .foregroundColor(.accentColor)
                            }

                            Spacer()

                            if engine.isFirmwareDownloading || engine.isFirmwareFlashing {
                                Button("Interrupt / Cancel") {
                                    engine.isFirmwareDownloading = false
                                    engine.isFirmwareFlashing = false
                                }
                                .controlSize(.small)
                            }
                        }

                        // Progress Bar
                        if engine.isFirmwareDownloading || engine.isFirmwareFlashing {
                            let prog = engine.firmwareFlashProgress > 0 ? engine.firmwareFlashProgress : engine.firmwareDownloadProgress
                            VStack(alignment: .leading, spacing: 3) {
                                ProgressView(value: prog > 0 ? prog : nil)
                                HStack {
                                    Text(engine.firmwareStatusMessage)
                                        .font(.caption2)
                                        .foregroundColor(.secondary)
                                    Spacer()
                                    if prog > 0 {
                                        Text("\(Int(prog * 100))%")
                                            .font(.caption2.bold().monospacedDigit())
                                            .foregroundColor(.accentColor)
                                    }
                                }
                            }
                        }

                        // Live Terminal Stream Log
                        if !engine.activeFirmwareLog.isEmpty {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Label("Live Flash Execution Terminal", systemImage: "terminal.fill")
                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                        .foregroundColor(.secondary)
                                    Spacer()
                                    Button("Copy Log") {
                                        let text = engine.activeFirmwareLog.joined(separator: "\n")
                                        NSPasteboard.general.clearContents()
                                        NSPasteboard.general.setString(text, forType: .string)
                                    }
                                    .controlSize(.mini)
                                    Button("Clear") {
                                        engine.activeFirmwareLog.removeAll()
                                    }
                                    .controlSize(.mini)
                                }

                                ScrollView {
                                    VStack(alignment: .leading, spacing: 2) {
                                        ForEach(engine.activeFirmwareLog.suffix(15), id: \.self) { line in
                                            Text(line)
                                                .font(.system(size: 10, design: .monospaced))
                                                .foregroundColor(line.contains("[SUCCESS]") ? .green : (line.contains("[ERROR]") || line.contains("ERROR") ? .red : (line.contains("[NOTICE]") ? .orange : .white)))
                                                .frame(maxWidth: .infinity, alignment: .leading)
                                        }
                                    }
                                    .padding(8)
                                }
                                .frame(height: 110)
                                .background(RoundedRectangle(cornerRadius: 6).fill(Color.black.opacity(0.85)))
                            }
                        }
                    }
                }
            }
            .padding(10)
        }
        .onAppear {
            if engine.activePlatform == .samsung && engine.samsungCloudFirmwares.isEmpty {
                Task { await engine.querySamsungCloudFirmwares() }
            }
        }
    }

    private var targetModelTitle: String {
        if let m = engine.samsungModemInfo?.model, !m.isEmpty { return m }
        if engine.activePlatform == .samsung, let um = engine.universalMatch?.modelNumber, !um.isEmpty { return um }
        return "No Samsung Device Connected"
    }
    private var deviceModeBadge: String {
        let hasOdin = engine.usbDevices.contains { $0.vendorId == 0x04e8 && ($0.productId == 0x685d || $0.productId == 0x6601) }
        if hasOdin { return "Odin Download Mode" }
        if engine.samsungModemInfo != nil { return "Samsung Modem / MTP" }
        return "Standby"
    }
    private var targetSerial: String {
        if let s = engine.samsungModemInfo?.serialNumber, !s.isEmpty { return s }
        if engine.activePlatform == .samsung, let us = engine.universalMatch?.serialOrUdid, us != "Unknown Serial" { return us }
        return "—"
    }
    private var targetPda: String {
        if let p = engine.samsungModemInfo?.pdaVersion, !p.isEmpty { return p }
        if engine.activePlatform == .samsung, let sp = engine.universalMatch?.stockFirmwareBuild, !sp.isEmpty { return sp }
        return "—"
    }
    private var targetBit: String {
        if let p = engine.samsungModemInfo?.pdaVersion, let bit = ServicingEngine.extractBootloaderBit(from: p) {
            return "Binary U:\(bit)"
        }
        return "Unverified"
    }
}

struct SamFwEmulationWorkbenchCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var selectedTab: Int = 0
    @State private var targetCarrierCsc: String = "XAA"
    @State private var showResetConfirmation: Bool = false

    let cscPresets = [
        ("XAA", "US Unlocked Retail"),
        ("TFN", "TracFone / Straight Talk / Verizon MVNO"),
        ("VZW", "Verizon Wireless"),
        ("TMB", "T-Mobile USA"),
        ("ATT", "AT&T USA"),
        ("EUX", "European Union Open"),
        ("XAR", "USA Wi-Fi Open")
    ]

    var body: some View {
        GroupBox(label: Label("Samsung Professional Servicing Workbench (SamFw Architecture)", systemImage: "wrench.and.screwdriver.fill")) {
            VStack(alignment: .leading, spacing: 12) {
                // Segmented Picker
                Picker("", selection: $selectedTab) {
                    Text("Test Mode AT Bridge (*#0*#)").tag(0)
                    Text("Carrier CSC Switch").tag(1)
                    Text("Factory Master Reset").tag(2)
                    Text("Diagnostic Codes & Reboot").tag(3)
                }
                .pickerStyle(.segmented)

                // Tab 0: Test Mode AT Diagnostic Bridge
                if selectedTab == 0 {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: "bolt.badge.clock.fill")
                                .font(.system(size: 24))
                                .foregroundColor(.orange)
                            VStack(alignment: .leading, spacing: 3) {
                                Text("Emergency Test Mode AT Diagnostic Bridge")
                                    .font(.system(size: 12.5, weight: .bold))
                                Text("Sends automated baseband AT sequences (AT+SWATD=0, AT+ACTIVATE, AT+DUMPENABLE, AT+KSTRINGB) over the USB modem port to enable high-speed USB debugging.")
                                    .font(.system(size: 11))
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.08)))

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Instructions:")
                                .font(.caption.weight(.bold))
                            Text("1. On the phone, go to the Emergency Call screen and dial *#0*# (or #*#88#*# on newer software).")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text("2. Click 'Execute Test Mode AT Sequence' below.")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text("3. Look at the phone screen: When 'Allow USB debugging?' appears, tap 'Always allow' and OK.")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        HStack(spacing: 10) {
                            Button {
                                Task { await engine.runSamsungTestModeAdbEnableSequence() }
                            } label: {
                                Label("Execute Test Mode AT Sequence (Enable ADB)", systemImage: "play.fill")
                                    .font(.system(size: 11.5, weight: .bold))
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.orange)
                            .disabled(engine.isBusy)

                            Button("Dial *#0*# Intent") {
                                Task {
                                    await engine.launchTargetIntent(
                                        title: "Open Hardware Test Menu",
                                        adbShellArgs: ["am start -a android.intent.action.DIAL -d 'tel:*%230*%23'"]
                                    )
                                }
                            }
                        }
                    }
                    .padding(6)
                }

                // Tab 1: Carrier CSC Firmware Switcher
                else if selectedTab == 1 {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: "globe.americas.fill")
                                .font(.system(size: 24))
                                .foregroundColor(.blue)
                            VStack(alignment: .leading, spacing: 3) {
                                Text("Carrier CSC Profile & Firmware Transition")
                                    .font(.system(size: 12.5, weight: .bold))
                                Text("Changes carrier CSC sales code and dispatches Samsung CID Manager Preconfig without wiping userdata when supported by the multi-CSC container.")
                                    .font(.system(size: 11))
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.blue.opacity(0.08)))

                        HStack(spacing: 8) {
                            Text("Quick Presets:")
                                .font(.caption.weight(.semibold))
                                .foregroundColor(.secondary)
                            ForEach(cscPresets.prefix(5), id: \.0) { item in
                                Button(item.0) {
                                    targetCarrierCsc = item.0
                                }
                                .controlSize(.small)
                            }
                        }

                        HStack(spacing: 10) {
                            Text("Target 3-Letter CSC:")
                                .font(.caption.weight(.semibold))
                            TextField("e.g. XAA, TFN, VZW", text: $targetCarrierCsc)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(size: 12, design: .monospaced))
                                .frame(width: 120)

                            Button {
                                Task { await engine.executeCscCarrierSwitch(targetCsc: targetCarrierCsc) }
                            } label: {
                                Label("Execute Carrier CSC Switch (\(targetCarrierCsc))", systemImage: "arrow.triangle.2.circlepath")
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(engine.isBusy)

                            Button("Open Preconfig (*#272*)") {
                                Task {
                                    await engine.launchTargetIntent(
                                        title: "Open Preconfig Activity",
                                        adbShellArgs: ["am start -n com.samsung.android.cidmanager/.modules.preconfig.PreconfigActivity"]
                                    )
                                }
                            }
                        }
                    }
                    .padding(6)
                }

                // Tab 2: Factory Master Reset & Provisioner
                else if selectedTab == 2 {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: "trash.circle.fill")
                                .font(.system(size: 24))
                                .foregroundColor(.red)
                            VStack(alignment: .leading, spacing: 3) {
                                Text("Authorized Factory Reset & Setup Provisioner")
                                    .font(.system(size: 12.5, weight: .bold))
                                Text("Executes standard MASTER_CLEAR system broadcast or baseband AT factory initialization, wiping cache and user partitions and resetting setup state.")
                                    .font(.system(size: 11))
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.red.opacity(0.08)))

                        HStack(spacing: 12) {
                            Button {
                                showResetConfirmation = true
                            } label: {
                                Label("1-Click Master Clear & Factory Reset", systemImage: "trash.fill")
                                    .font(.system(size: 11.5, weight: .bold))
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.red)
                            .disabled(engine.isBusy)

                            Button("Initialize Provisioning Flags (Setup Complete = 1)") {
                                Task {
                                    _ = await engine.executeAndLog(
                                        workflowId: "samsung.provision_flags",
                                        title: "Initialize Setup & Provisioning Flags",
                                        executable: engine.toolPaths["adb"]!,
                                        arguments: engine.adbArgs(["shell", "settings put global device_provisioned 1; settings put secure user_setup_complete 1"])
                                    )
                                }
                            }
                        }
                    }
                    .padding(6)
                    .alert("Confirm Factory Reset", isPresented: $showResetConfirmation) {
                        Button("Cancel", role: .cancel) { }
                        Button("Wipe & Reset", role: .destructive) {
                            Task { await engine.executeFactoryProvisioningReset() }
                        }
                    } message: {
                        Text("This will send an authorized Master Clear to the connected Samsung device. All user storage and installed applications will be wiped.")
                    }
                }

                // Tab 3: Diagnostic Codes & Reboots
                else if selectedTab == 3 {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Samsung Hardware Diagnostic Codes (MTP / ADB Intent):")
                            .font(.caption.weight(.bold))

                        HStack(spacing: 8) {
                            Button("Test Mode (*#0*#)") {
                                Task { await engine.launchTargetIntent(title: "Hardware Test Mode", adbShellArgs: ["am start -a android.intent.action.DIAL -d 'tel:*%230*%23'"]) }
                            }
                            Button("USB Config (*#0808#)") {
                                Task { await engine.launchTargetIntent(title: "USB Settings", adbShellArgs: ["am start -a android.intent.action.DIAL -d 'tel:*%230808%23'"]) }
                            }
                            Button("SysDump Log (*#9900#)") {
                                Task { await engine.launchTargetIntent(title: "SysDump Logcat", adbShellArgs: ["am start -a android.intent.action.DIAL -d 'tel:*%239900%23'"]) }
                            }
                            Button("Battery Gauge (*#0228#)") {
                                Task { await engine.launchTargetIntent(title: "Battery Fuel Gauge", adbShellArgs: ["am start -a android.intent.action.DIAL -d 'tel:*%230228%23'"]) }
                            }
                            Button("ServiceMode (*#0011#)") {
                                Task { await engine.launchTargetIntent(title: "ServiceMode RIL", adbShellArgs: ["am start -a android.intent.action.DIAL -d 'tel:*%230011%23'"]) }
                            }
                        }

                        Divider()

                        Text("Device Reboot Controls:")
                            .font(.caption.weight(.bold))

                        HStack(spacing: 10) {
                            Button("Reboot Normal") {
                                Task { await engine.rebootSamsungTargetToMode("normal") }
                            }
                            Button("Reboot Download Mode (Odin)") {
                                Task { await engine.rebootSamsungTargetToMode("download") }
                            }
                            Button("Reboot Recovery Mode") {
                                Task { await engine.rebootSamsungTargetToMode("recovery") }
                            }
                        }

                        Divider()

                        HStack(spacing: 10) {
                            Button("Disable Samsung OTA Updates") {
                                Task {
                                    _ = await engine.executeAndLog(
                                        workflowId: "samsung.disable_ota",
                                        title: "Disable Samsung OTA",
                                        executable: engine.toolPaths["adb"]!,
                                        arguments: engine.adbArgs(["shell", "pm disable-user --user 0 com.wssyncmldm; pm disable-user --user 0 com.sec.android.soagent"])
                                    )
                                }
                            }
                            Button("Enable Samsung OTA Updates") {
                                Task {
                                    _ = await engine.executeAndLog(
                                        workflowId: "samsung.enable_ota",
                                        title: "Enable Samsung OTA",
                                        executable: engine.toolPaths["adb"]!,
                                        arguments: engine.adbArgs(["shell", "pm enable com.wssyncmldm; pm enable com.sec.android.soagent"])
                                    )
                                }
                            }
                        }
                    }
                    .padding(6)
                }
            }
            .padding(10)
        }
    }
}

// MARK: - Apple Component Verification & Battery Telemetry Studio Card (3uTools alternative on macOS)

struct AppleHardwareAuditStudioCard: View {
    @ObservedObject var engine: ServicingEngine

    var body: some View {
        GroupBox(label: Label("Apple Component Verification & Battery Telemetry Studio (3uTools Engine)", systemImage: "stethoscope")) {
            VStack(alignment: .leading, spacing: 12) {
                // Action Header Bar
                HStack(alignment: .center) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Comprehensive Hardware Audit & Anti-Tampering Inspection")
                            .font(.system(size: 12, weight: .bold))
                        Text("Verifies physical battery cycle degradation, current/design mAh, factory logic board serial matching & crash logs.")
                            .font(.system(size: 10.5))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Button {
                        Task { _ = await engine.queryAppleHardwareAudit() }
                    } label: {
                        if engine.isAuditingAppleHardware {
                            ProgressView().controlSize(.small).padding(.trailing, 2)
                        }
                        Label("Run 3uTools-Grade Hardware Audit", systemImage: "sparkles")
                            .font(.system(size: 11, weight: .semibold))
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.indigo)
                    .disabled(engine.isAuditingAppleHardware)
                }
                .padding(8)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color.indigo.opacity(0.07)))

                if let audit = engine.appleHardwareAudit {
                    // Battery & Device Health Telemetry Metrics
                    HStack(spacing: 12) {
                        // Metric 1: Battery Health %
                        VStack(spacing: 3) {
                            Text("\(audit.batteryHealthPercentage)%")
                                .font(.system(size: 24, weight: .bold, design: .rounded))
                                .foregroundColor(audit.batteryHealthPercentage >= 80 ? .green : .red)
                            Text("Battery Health")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                        }
                        .frame(minWidth: 100)
                        .padding(.vertical, 8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))

                        // Metric 2: Cycle Count
                        VStack(spacing: 3) {
                            Text("\(audit.batteryCycleCount)")
                                .font(.system(size: 24, weight: .bold, design: .rounded))
                                .foregroundColor(.primary)
                            Text("Charge Cycles")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                        }
                        .frame(minWidth: 100)
                        .padding(.vertical, 8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))

                        // Metric 3: Capacity
                        VStack(spacing: 3) {
                            Text("\(audit.batteryCurrentCapacityMah) / \(audit.batteryDesignCapacityMah) mAh")
                                .font(.system(size: 15, weight: .bold, design: .monospaced))
                                .foregroundColor(.blue)
                                .padding(.top, 4)
                            Text("Current / Design Capacity")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))

                        // Metric 4: Panic Logs
                        VStack(spacing: 3) {
                            Text("\(audit.panicLogsCount)")
                                .font(.system(size: 24, weight: .bold, design: .rounded))
                                .foregroundColor(audit.panicLogsCount == 0 ? .green : .orange)
                            Text(audit.panicLogsCount == 0 ? "Panics: 0" : "\(audit.panicLogsCount) Panics")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.secondary)
                        }
                        .frame(minWidth: 100)
                        .padding(.vertical, 8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                    }

                    // Component Serial Matching Table
                    VStack(alignment: .leading, spacing: 6) {
                        Text("OEM Factory Component Serial Verification:")
                            .font(.system(size: 11, weight: .bold))

                        VStack(spacing: 4) {
                            ForEach(audit.components) { comp in
                                HStack {
                                    Image(systemName: comp.isMatch ? "checkmark.seal.fill" : "exclamationmark.triangle.fill")
                                        .foregroundColor(comp.isMatch ? .green : .orange)
                                        .font(.system(size: 12))

                                    Text(comp.componentName)
                                        .font(.system(size: 11, weight: .medium))
                                        .frame(width: 170, alignment: .leading)

                                    Text("Factory: \(comp.factorySerial)")
                                        .font(.system(size: 10, design: .monospaced))
                                        .foregroundColor(.secondary)
                                        .lineLimit(1)

                                    Spacer()

                                    Text(comp.status)
                                        .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 1.5)
                                        .background(RoundedRectangle(cornerRadius: 3).fill(comp.isMatch ? Color.green.opacity(0.18) : Color.orange.opacity(0.18)))
                                        .foregroundColor(comp.isMatch ? .green : .orange)
                                }
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(RoundedRectangle(cornerRadius: 4).fill(Color.primary.opacity(0.02)))
                            }
                        }
                    }
                    .padding(8)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))

                    // Apple Kernel Panic Log Hardware Fault Diagnosis (3uTools Killer)
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Apple Kernel Panic Log Hardware Fault Diagnosis:")
                                .font(.system(size: 11, weight: .bold))
                            Spacer()
                            Text("\(audit.panicFaults.count) diagnosis item(s)")
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(.secondary)
                        }

                        VStack(spacing: 6) {
                            ForEach(audit.panicFaults) { fault in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        HStack(spacing: 6) {
                                            Image(systemName: fault.severity.contains("PASS") ? "checkmark.circle.fill" : "exclamationmark.octagon.fill")
                                                .foregroundColor(fault.severity.contains("PASS") ? .green : (fault.severity.contains("CRITICAL") ? .red : .orange))
                                                .font(.system(size: 12))
                                            Text(fault.suspectHardware)
                                                .font(.system(size: 11, weight: .bold))
                                                .foregroundColor(.primary)
                                        }

                                        Spacer()

                                        Text(fault.severity)
                                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 1.5)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(fault.severity.contains("PASS") ? Color.green.opacity(0.18) : Color.red.opacity(0.18)))
                                            .foregroundColor(fault.severity.contains("PASS") ? .green : .red)
                                    }

                                    Text("Crash Signature: \(fault.panicReasonSnippet)")
                                        .font(.system(size: 10, design: .monospaced))
                                        .foregroundColor(.secondary)

                                    HStack(alignment: .top, spacing: 4) {
                                        Image(systemName: "wrench.and.screwdriver")
                                            .font(.system(size: 9.5))
                                            .foregroundColor(.blue)
                                            .padding(.top, 1)
                                        Text("Actionable Repair: \(fault.actionableRepairGuide)")
                                            .font(.system(size: 10.5))
                                            .foregroundColor(.blue)
                                    }
                                }
                                .padding(8)
                                .background(RoundedRectangle(cornerRadius: 5).fill(Color.primary.opacity(0.02)))
                            }
                        }
                    }
                    .padding(8)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                } else {
                    HStack(spacing: 10) {
                        Image(systemName: "info.circle")
                            .foregroundColor(.secondary)
                        Text("Connect an iPhone or iPad via USB and click 'Run 3uTools-Grade Hardware Audit' to analyze battery wear, inspect OEM serials, and decrypt panic logs.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                    .padding(8)
                }
            }
            .padding(6)
        }
    }
}

// MARK: - Hardware Test-Point Pinout & Motherboard Schematic Database Card

struct HardwareTestPointPinoutCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var selectedTestPointId: String = "tp_a16_5g"

    var activeEntry: HardwareTestPointEntry {
        HardwareTestPointEntry.standardTestPoints.first(where: { $0.id == selectedTestPointId }) ?? HardwareTestPointEntry.standardTestPoints[0]
    }

    var body: some View {
        GroupBox(label: Label("Hardware Test-Point & Motherboard Schematic Database (BROM / EDL 9008)", systemImage: "point.filled.topleft.down.curvedto.point.bottomright.up")) {
            VStack(alignment: .leading, spacing: 12) {
                // Header & Model Selector
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Emergency CPU Bootrom Pinout & Test-Point Locator")
                            .font(.system(size: 12, weight: .bold))
                        Text("Physical PCB GND test points to recover completely hard-bricked Snapdragon, MediaTek, and Exynos devices.")
                            .font(.system(size: 10.5))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Picker("Device Model:", selection: $selectedTestPointId) {
                        ForEach(HardwareTestPointEntry.standardTestPoints) { tp in
                            Text("\(tp.marketName) (\(tp.modelName))").tag(tp.id)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 310)
                }
                .padding(8)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.06)))

                // Schematic & Pinout Details Display
                HStack(alignment: .top, spacing: 16) {
                    // Left: Motherboard Schematic Visual Simulation
                    VStack(spacing: 8) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color(red: 0.08, green: 0.16, blue: 0.12)) // PCB Green
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.green.opacity(0.3), lineWidth: 1.5)
                                )

                            VStack(spacing: 10) {
                                HStack {
                                    Text("PCB REV 1.0")
                                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                                        .foregroundColor(.green.opacity(0.6))
                                    Spacer()
                                    Text("CHIP: \(activeEntry.chipset)")
                                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                                        .foregroundColor(.yellow.opacity(0.8))
                                        .lineLimit(1)
                                }
                                .padding(.horizontal, 10)
                                .padding(.top, 6)

                                // Schematic chips
                                HStack(spacing: 14) {
                                    // SoC Metal Shield
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 4)
                                            .fill(Color.gray.opacity(0.35))
                                            .frame(width: 78, height: 65)
                                        Text("CPU / RAM")
                                            .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                                            .foregroundColor(.white.opacity(0.8))
                                    }

                                    // Flash UFS / eMMC
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 4)
                                            .fill(Color.gray.opacity(0.25))
                                            .frame(width: 65, height: 58)
                                        Text("UFS 2.2")
                                            .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                                            .foregroundColor(.white.opacity(0.7))
                                    }

                                    // Labeled Test Point Pad with indicator
                                    VStack(spacing: 3) {
                                        Circle()
                                            .fill(Color.yellow)
                                            .frame(width: 14, height: 14)
                                            .overlay(
                                                Circle()
                                                    .stroke(Color.red, lineWidth: 2)
                                            )
                                        Text("TEST POINT")
                                            .font(.system(size: 7.5, weight: .heavy, design: .monospaced))
                                            .foregroundColor(.yellow)
                                        Text("SHORT TO GND")
                                            .font(.system(size: 7, design: .monospaced))
                                            .foregroundColor(.white.opacity(0.7))
                                    }
                                }
                                .padding(.vertical, 4)

                                HStack {
                                    Text("GND SHIELD FRAME")
                                        .font(.system(size: 7.5, weight: .semibold, design: .monospaced))
                                        .foregroundColor(.white.opacity(0.5))
                                    Spacer()
                                    Text(activeEntry.forceMode)
                                        .font(.system(size: 7.5, weight: .bold, design: .monospaced))
                                        .foregroundColor(.cyan)
                                }
                                .padding(.horizontal, 10)
                                .padding(.bottom, 6)
                            }
                        }
                        .frame(width: 320, height: 135)

                        HStack(spacing: 6) {
                            Image(systemName: "pin.fill")
                                .foregroundColor(.yellow)
                                .font(.system(size: 11))
                            Text("Target: \(activeEntry.testPointGndShortTarget)")
                                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                                .foregroundColor(.primary)
                        }
                    }

                    // Right: Instructions & Steps
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(activeEntry.marketName)
                                .font(.system(size: 13, weight: .bold))
                            Spacer()
                            Text(activeEntry.forceMode)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 1.5)
                                .background(RoundedRectangle(cornerRadius: 3).fill(Color.blue.opacity(0.18)))
                                .foregroundColor(.blue)
                        }

                        Text("Chipset: \(activeEntry.chipset) · Engine: \(activeEntry.referenceOemTools)")
                            .font(.system(size: 10.5, design: .monospaced))
                            .foregroundColor(.secondary)

                        Divider()

                        Text("Tweezer Short & USB Plug-In Sequence:")
                            .font(.system(size: 11, weight: .bold))

                        Text(activeEntry.pinoutInstructions)
                            .font(.system(size: 10.5))
                            .foregroundColor(.primary)
                            .lineSpacing(3)
                    }
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
            }
            .padding(6)
        }
    }
}

// MARK: - Universal Android OTA payload.bin Dumper & Partition Extractor Card

struct PayloadBinExtractorStudioCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var inputFilePath: String = ""
    @State private var selectedPartitions: Set<String> = ["boot", "init_boot", "vendor_boot", "vbmeta"]

    var body: some View {
        GroupBox(label: Label("Universal Android OTA payload.bin Dumper & Partition Extractor", systemImage: "shippingbox.and.arrow.backward.fill")) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Ingests OTA zip archives or uncompressed payload.bin files from Google Pixel, OnePlus, Motorola, Xiaomi, and generic Android updates. Extracts raw partition images without requiring external Python packages.")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                HStack(spacing: 10) {
                    TextField("Select payload.bin or OTA update .zip archive...", text: $inputFilePath)
                        .textFieldStyle(.roundedBorder)
                        .font(.system(size: 12, design: .monospaced))

                    Button("Browse Archive...") {
                        if let path = pickFile(allowedExtensions: ["bin", "zip"]) {
                            inputFilePath = path
                            Task { await engine.inspectPayloadArchive(path: path) }
                        }
                    }

                    Button("Inspect Manifest") {
                        guard !inputFilePath.isEmpty else { return }
                        Task { await engine.inspectPayloadArchive(path: inputFilePath) }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(inputFilePath.isEmpty || engine.isDumpingPayload)
                }

                if !engine.discoveredPayloadPartitions.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Partitions Discovered in Manifest (\(engine.discoveredPayloadPartitions.count)):")
                                .font(.system(size: 11.5, weight: .bold))
                            Spacer()
                            Button("Select Boot Only") {
                                selectedPartitions = Set(engine.discoveredPayloadPartitions.filter { $0.isCriticalBoot }.map { $0.name })
                            }
                            .controlSize(.small)
                            Button("Select All") {
                                selectedPartitions = Set(engine.discoveredPayloadPartitions.map { $0.name })
                            }
                            .controlSize(.small)
                        }

                        ScrollView(.vertical, showsIndicators: true) {
                            LazyVGrid(columns: [GridItem(.adaptive(minimum: 140))], spacing: 6) {
                                ForEach(engine.discoveredPayloadPartitions) { part in
                                    let isChecked = selectedPartitions.contains(part.name)
                                    Button {
                                        if isChecked {
                                            selectedPartitions.remove(part.name)
                                        } else {
                                            selectedPartitions.insert(part.name)
                                        }
                                    } label: {
                                        HStack(spacing: 6) {
                                            Image(systemName: isChecked ? "checkmark.square.fill" : "square")
                                                .foregroundColor(isChecked ? .accentColor : .secondary)
                                            VStack(alignment: .leading, spacing: 1) {
                                                Text(part.name)
                                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                                    .foregroundColor(.primary)
                                                Text(part.formattedSize)
                                                    .font(.system(size: 9.5))
                                                    .foregroundColor(.secondary)
                                            }
                                            Spacer()
                                        }
                                        .padding(6)
                                        .background(RoundedRectangle(cornerRadius: 4).fill(isChecked ? Color.accentColor.opacity(0.08) : Color(NSColor.controlBackgroundColor)))
                                        .overlay(RoundedRectangle(cornerRadius: 4).stroke(isChecked ? Color.accentColor : Color.secondary.opacity(0.2), lineWidth: 1))
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                        .frame(maxHeight: 140)

                        if engine.isDumpingPayload {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    ProgressView(value: engine.payloadDumpProgress)
                                        .progressViewStyle(.linear)
                                    Text("\(Int(engine.payloadDumpProgress * 100))%")
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        .foregroundColor(.accentColor)
                                }
                                if !engine.payloadStatusMessage.isEmpty {
                                    Text(engine.payloadStatusMessage)
                                        .font(.system(size: 10.5, design: .monospaced))
                                        .foregroundColor(.secondary)
                                }
                            }
                            .padding(8)
                            .background(RoundedRectangle(cornerRadius: 6).fill(Color.accentColor.opacity(0.08)))
                        }

                        HStack(spacing: 12) {
                            Button {
                                Task {
                                    await engine.extractPayloadPartitions(path: inputFilePath, selectedPartitionNames: Array(selectedPartitions))
                                }
                            } label: {
                                Label("⚡ Extract Selected Partitions (\(selectedPartitions.count))", systemImage: "arrow.down.doc.fill")
                                    .font(.system(size: 11.5, weight: .bold))
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(selectedPartitions.isEmpty || engine.isDumpingPayload)

                            Button {
                                let bootTargets = engine.discoveredPayloadPartitions.filter { $0.isCriticalBoot }.map { $0.name }
                                Task {
                                    await engine.extractPayloadPartitions(path: inputFilePath, selectedPartitionNames: bootTargets)
                                }
                            } label: {
                                Label("⚡ 1-Click Extract Boot & Init_Boot (KernelSU / Root Patch)", systemImage: "flame.fill")
                                    .font(.system(size: 11.5, weight: .bold))
                            }
                            .buttonStyle(.bordered)
                            .tint(.orange)
                            .disabled(engine.isDumpingPayload)

                            Spacer()

                            Button("Open Extracted Folder in Finder") {
                                let dir = "\(NSHomeDirectory())/Downloads/BobFWTools_Extracted"
                                try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
                                NSWorkspace.shared.open(URL(fileURLWithPath: dir))
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                    .padding(8)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                }
            }
            .padding(8)
        }
    }
}

// MARK: - Fastbootd Dynamic Partition & Slot A/B Manager Card

struct FastbootdLogicalPartitionManagerCard: View {
    @ObservedObject var engine: ServicingEngine

    var body: some View {
        GroupBox(label: Label("Fastbootd Dynamic Partition & Slot A/B Manager (Android 10 - 16)", systemImage: "slider.horizontal.2.square.badge.arrow.down")) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Manage Virtual A/B active boot slots and transition between standard Bootloader (ABOOT) and Userspace Fastbootd to access dynamic logical partitions (system, vendor, product, odm).")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                HStack(spacing: 16) {
                    // Active Slot Indicator & Switcher
                    VStack(alignment: .leading, spacing: 4) {
                        Text("ACTIVE BOOT SLOT:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)

                        HStack(spacing: 8) {
                            Text("Slot: \(engine.fastbootCurrentSlot.uppercased())")
                                .font(.system(size: 13, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(RoundedRectangle(cornerRadius: 4).fill(Color.blue.opacity(0.18)))
                                .foregroundColor(.blue)

                            Button("Switch to Slot _a") {
                                Task { _ = await engine.switchFastbootActiveSlot(targetSlot: "a") }
                            }
                            .disabled(engine.fastbootCurrentSlot == "a" || engine.isSwitchingFastbootSlot)

                            Button("Switch to Slot _b") {
                                Task { _ = await engine.switchFastbootActiveSlot(targetSlot: "b") }
                            }
                            .disabled(engine.fastbootCurrentSlot == "b" || engine.isSwitchingFastbootSlot)

                            Button("Query Slot") {
                                Task { await engine.queryFastbootSlotAndPartitions() }
                            }
                        }
                    }

                    Spacer()

                    // Fastbootd Transition Engine
                    VStack(alignment: .trailing, spacing: 4) {
                        Text("DYNAMIC PARTITION BRIDGE:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)

                        Button {
                            Task { _ = await engine.rebootToFastbootd() }
                        } label: {
                            Label("⚡ Reboot to Userspace Fastbootd", systemImage: "arrow.triangle.2.circlepath.circle.fill")
                                .font(.system(size: 11.5, weight: .bold))
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.indigo)
                    }
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
            }
            .padding(6)
        }
    }
}

// MARK: - Multi-Brand Hardware Diagnostic Codes & Secret Menu Hub Card

struct MultiBrandHardwareDiagnosticHubCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var selectedBrand: String = "Google Pixel"

    let brands = ["Google Pixel", "Xiaomi / POCO", "Motorola", "Qualcomm Diag"]

    var filteredCodes: [MultiBrandSecretCode] {
        engine.multiBrandCodes.filter { $0.brand == selectedBrand }
    }

    var body: some View {
        GroupBox(label: Label("Multi-Brand Hardware Diagnostic Codes & Secret Menu Launcher", systemImage: "asterisk.circle.fill")) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Standardized dialer codes and hardware test intents across all major non-Samsung OEMs. Launch directly over ADB or trigger manually on device.")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                Picker("OEM Brand:", selection: $selectedBrand) {
                    ForEach(brands, id: \.self) { b in
                        Text(b).tag(b)
                    }
                }
                .pickerStyle(.segmented)

                VStack(spacing: 8) {
                    ForEach(filteredCodes) { item in
                        HStack(alignment: .top, spacing: 12) {
                            VStack(alignment: .leading, spacing: 3) {
                                HStack(spacing: 8) {
                                    Text(item.title)
                                        .font(.system(size: 12, weight: .bold))
                                        .foregroundColor(.primary)

                                    Text(item.code)
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 1)
                                        .background(RoundedRectangle(cornerRadius: 3).fill(Color.orange.opacity(0.18)))
                                        .foregroundColor(.orange)

                                    Text(item.targetSubsystem)
                                        .font(.system(size: 9.5, weight: .medium, design: .monospaced))
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 1)
                                        .background(RoundedRectangle(cornerRadius: 3).fill(Color.blue.opacity(0.14)))
                                        .foregroundColor(.blue)
                                }

                                Text(item.description)
                                    .font(.system(size: 10.5))
                                    .foregroundColor(.secondary)
                            }

                            Spacer()

                            Button {
                                Task { _ = await engine.dispatchSecretCodeOverAdb(code: item.code) }
                            } label: {
                                Label("⚡ Launch (ADB)", systemImage: "play.circle.fill")
                                    .font(.system(size: 10.5, weight: .bold))
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.accentColor)
                            .controlSize(.small)
                            .disabled(!engine.devices.contains { $0.transport == .adb })

                            Button {
                                NSPasteboard.general.clearContents()
                                NSPasteboard.general.setString(item.code, forType: .string)
                                engine.log(.info, "Copied '\(item.code)' to clipboard.")
                            } label: {
                                Image(systemName: "doc.on.doc")
                            }
                            .controlSize(.small)
                            .help("Copy code to clipboard")
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                    }
                }
            }
            .padding(6)
        }
    }
}

// MARK: - Samsung Download Mode Screen Telemetry & Preflight Decrypter Card

struct SamsungDownloadScreenTelemetryCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var isExpanded: Bool = false

    var body: some View {
        GroupBox(label: Label("Samsung Download Mode Screen Telemetry & Preflight Decrypter", systemImage: "text.magnifyingglass")) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Live Decoder for On-Screen Knox, Rollback & Lock Security Counters")
                            .font(.system(size: 11.5, weight: .bold))
                        Text("Explains on-screen flags (KG STATUS, RP SWREV, WARRANTY VOID) to avoid flash failure before writing to NAND.")
                            .font(.system(size: 10.5))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Button(isExpanded ? "Collapse Guide" : "Expand All Flags (6)") {
                        isExpanded.toggle()
                    }
                    .controlSize(.small)
                }

                if isExpanded {
                    VStack(spacing: 6) {
                        ForEach(engine.samsungScreenFlags) { flag in
                            VStack(alignment: .leading, spacing: 3) {
                                HStack(spacing: 8) {
                                    Text(flag.flagName)
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        .foregroundColor(.primary)

                                    Text(flag.valuesExplained)
                                        .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 1)
                                        .background(RoundedRectangle(cornerRadius: 3).fill(Color.orange.opacity(0.18)))
                                        .foregroundColor(.orange)

                                    Spacer()
                                }

                                Text(flag.diagnosticMeaning)
                                    .font(.system(size: 10))
                                    .foregroundColor(.secondary)

                                HStack(alignment: .top, spacing: 4) {
                                    Image(systemName: "lightbulb.fill")
                                        .font(.system(size: 9))
                                        .foregroundColor(.green)
                                        .padding(.top, 1)
                                    Text("Technician Advice: \(flag.repairShopAdvice)")
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(.green)
                                }
                            }
                            .padding(8)
                            .background(RoundedRectangle(cornerRadius: 5).fill(Color.primary.opacity(0.02)))
                        }
                    }
                    .padding(4)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                }
            }
            .padding(6)
        }
    }
}

// MARK: - Universal Recovery Mode ADB Sideload Flasher Card

struct AdbRecoverySideloadCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var otaPackagePath: String = ""

    var body: some View {
        GroupBox(label: Label("Universal Recovery Mode ADB Sideload Flasher (Android Recovery 3e)", systemImage: "arrow.up.bin.fill")) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Flash official rescue OTA update packages (.zip) to any Android device bootlooping in stock Recovery. On phone, select 'Apply update from ADB' prior to dispatching.")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                HStack(spacing: 10) {
                    TextField("Select official recovery update .zip package...", text: $otaPackagePath)
                        .textFieldStyle(.roundedBorder)
                        .font(.system(size: 12, design: .monospaced))

                    Button("Browse OTA ZIP...") {
                        if let path = pickFile(allowedExtensions: ["zip"]) {
                            otaPackagePath = path
                        }
                    }

                    Button {
                        guard !otaPackagePath.isEmpty else { return }
                        Task { _ = await engine.executeAdbSideload(otaZipPath: otaPackagePath) }
                    } label: {
                        if engine.isSideloading {
                            ProgressView().controlSize(.small).padding(.trailing, 2)
                        }
                        Label("⚡ 1-Click ADB Sideload", systemImage: "bolt.fill")
                            .font(.system(size: 12, weight: .bold))
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.indigo)
                    .disabled(otaPackagePath.isEmpty || engine.isSideloading)
                }

                if engine.isSideloading {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            ProgressView(value: engine.sideloadProgress)
                                .progressViewStyle(.linear)
                            Text("\(Int(engine.sideloadProgress * 100))%")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundColor(.indigo)
                        }
                        if !engine.sideloadStatusText.isEmpty {
                            Text(engine.sideloadStatusText)
                                .font(.system(size: 10.5, design: .monospaced))
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(8)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color.indigo.opacity(0.08)))
                }
            }
            .padding(6)
        }
    }
}

// MARK: - Wireless ADB Pair & Connect Card (Android 11 - 16)

struct WirelessAdbBridgeCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var hostIp: String = "192.168.1."
    @State private var pairingPort: String = "37451"
    @State private var pairingCode: String = ""
    @State private var connectPort: String = "5555"

    var body: some View {
        GroupBox(label: Label("Wireless ADB Pair & Connect Bridge (Android 11 - 16)", systemImage: "wifi.circle.fill")) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Bypasses damaged, loose, or liquid-damaged USB-C ports by pairing directly over shop Wi-Fi network. On phone: Settings ➔ Developer Options ➔ Wireless Debugging ➔ Pair device with pairing code.")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Device IP Address:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)
                        TextField("e.g. 192.168.1.150", text: $hostIp)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11, design: .monospaced))
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("Pairing Port:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)
                        TextField("Port", text: $pairingPort)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11, design: .monospaced))
                            .frame(width: 80)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("6-Digit Pairing Code:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)
                        TextField("Code", text: $pairingCode)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11, design: .monospaced))
                            .frame(width: 100)
                    }

                    Button {
                        guard let p = Int(pairingPort), !hostIp.isEmpty, !pairingCode.isEmpty else { return }
                        Task { _ = await engine.pairWirelessAdb(host: hostIp, port: p, code: pairingCode) }
                    } label: {
                        Label("⚡ Pair (adb pair)", systemImage: "link.badge.plus")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.blue)
                    .disabled(engine.isWirelessAdbBusy || pairingCode.isEmpty)
                }

                Divider()

                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Connect Port (Default 5555 or dynamic):")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)
                        TextField("5555", text: $connectPort)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11, design: .monospaced))
                            .frame(width: 100)
                    }

                    Button {
                        guard let cp = Int(connectPort), !hostIp.isEmpty else { return }
                        Task { _ = await engine.connectWirelessAdb(host: hostIp, port: cp) }
                    } label: {
                        Label("🔗 Connect (adb connect)", systemImage: "antenna.radiowaves.left.and.right")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .buttonStyle(.bordered)
                    .disabled(engine.isWirelessAdbBusy || hostIp.isEmpty)

                    Spacer()

                    if !engine.wirelessAdbStatusText.isEmpty {
                        Text(engine.wirelessAdbStatusText)
                            .font(.system(size: 10.5, design: .monospaced))
                            .foregroundColor(.blue)
                    }
                }
            }
            .padding(6)
        }
    }
}

// MARK: - Apple Enterprise MDM & Supervision Clearance Preflight Card

struct AppleMdmClearanceCard: View {
    @ObservedObject var engine: ServicingEngine

    var body: some View {
        GroupBox(label: Label("Enterprise MDM & Apple Business Manager Clearance Preflight", systemImage: "building.2.crop.circle.fill")) {
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .center) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Intake Preflight: Apple School Manager & Corporate MDM Profile Inspection")
                            .font(.system(size: 11.5, weight: .bold))
                        Text("Queries com.apple.mobile.chaperone and CloudConfiguration to detect remote corporate management before customer intake.")
                            .font(.system(size: 10.5))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Button {
                        Task { _ = await engine.queryAppleMdmSupervision() }
                    } label: {
                        if engine.isCheckingAppleMdm {
                            ProgressView().controlSize(.small).padding(.trailing, 2)
                        }
                        Label("Run MDM Clearance Audit", systemImage: "checkmark.shield")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.indigo)
                    .disabled(engine.isCheckingAppleMdm)
                }
                .padding(8)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color.indigo.opacity(0.06)))

                if let report = engine.appleMdmReport {
                    HStack(spacing: 14) {
                        VStack(spacing: 2) {
                            Text(report.isSupervised ? "SUPERVISED" : "CLEAN")
                                .font(.system(size: 16, weight: .bold, design: .monospaced))
                                .foregroundColor(report.isSupervised ? .red : .green)
                            Text("Supervision Status")
                                .font(.system(size: 9.5))
                                .foregroundColor(.secondary)
                        }
                        .frame(minWidth: 120)
                        .padding(6)
                        .background(RoundedRectangle(cornerRadius: 5).fill(Color(NSColor.controlBackgroundColor)))

                        VStack(alignment: .leading, spacing: 2) {
                            Text("Organization: \(report.organizationName)")
                                .font(.system(size: 11, weight: .semibold))
                            Text(report.summaryText)
                                .font(.system(size: 10))
                                .foregroundColor(report.isSupervised ? .red : .secondary)
                        }
                        Spacer()
                    }
                    .padding(8)
                    .background(RoundedRectangle(cornerRadius: 6).fill(report.isSupervised ? Color.red.opacity(0.08) : Color.green.opacity(0.08)))
                }
            }
            .padding(6)
        }
    }
}

struct SamsungSuiteView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var customATCommand: String = "AT+DEVCONINFO"
    @State private var cscFrom: String = "EUX"
    @State private var targetCscCode: String = "XAR"
    @State private var stage1Carrier: String = "EUX (European Union Open)"
    @State private var stage2Carrier: String = "XAR (USA Wi-Fi Open)"
    @State private var stage3Carrier: String = "EUX (European Union Open)"
    @State private var trialFirmwarePath: String = ""
    @State private var customLaunchUrl: String = "https://www.google.com"

    var carrierOptions: [String] {
        CscFallbackRegistry.allProfiles.map { "\($0.code) (\($0.region))" }
    }

    var cscShortCodes: [String] {
        CscFallbackRegistry.allProfiles.map { $0.code }
    }

    @State private var flashItems: [PartitionFlashItem] = [
        PartitionFlashItem(enabled: true, partitionName: "BOOT", filePath: ""),
        PartitionFlashItem(enabled: false, partitionName: "RECOVERY", filePath: ""),
        PartitionFlashItem(enabled: false, partitionName: "SUPER", filePath: ""),
        PartitionFlashItem(enabled: false, partitionName: "SYSTEM", filePath: ""),
        PartitionFlashItem(enabled: false, partitionName: "VENDOR", filePath: ""),
        PartitionFlashItem(enabled: false, partitionName: "RADIO", filePath: "")
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ModuleHeader(
                title: "BobFWTools Samsung Servicing & Odin Flash Planner",
                subtitle: "Direct DTR/RTS USB Modem AT diagnostics, CSC preflight qualification, ADB servicing, and Odin/Heimdall flashing"
            )

            if engine.activePlatform != .samsung {
                HStack(spacing: 10) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.system(size: 16))
                    VStack(alignment: .leading, spacing: 2) {
                        Text("NO SAMSUNG GALAXY DEVICE DETECTED ON USB BUS")
                            .font(.system(size: 11.5, weight: .bold))
                            .foregroundColor(.orange)
                        Text("Samsung Modem AT operations, CSC carrier transitions, and Odin partition flash functions are disabled until a Samsung Galaxy target (VID 04e8) is connected.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 8).fill(Color.orange.opacity(0.12)))
            }

            // Section 0: Autonomous 1-Click Samsung Cloud Firmware Hub & Odin Flasher
            SamsungCloudFirmwareHubCard(engine: engine)

            // Section 0A: Download Mode Screen Telemetry & Security Counter Decoder
            SamsungDownloadScreenTelemetryCard(engine: engine)

            // Section 0B: Samsung Professional Servicing Workbench (SamFw Architecture)
            SamFwEmulationWorkbenchCard(engine: engine)

            // Section 0C: Hardware Test-Point Pinout & Schematics Database
            HardwareTestPointPinoutCard(engine: engine)

            // Guided Step-by-Step Servicing Pipeline Wizard
            GuidedWorkflowWizardCard(
                title: "Samsung Guided Carrier & Servicing Wizard",
                subtitle: "Enforces Step-by-Step isolation: Port Discovery -> AT Handshake -> Carrier Preflight -> Intent Dispatch",
                icon: "arrow.triangle.2.circlepath.circle.fill",
                steps: engine.samsungWizardSteps,
                onExecuteStep: { step in
                    Task { await engine.executeSamsungWizardStep(stepNumber: step, targetCsc: targetCscCode) }
                },
                onReset: {
                    engine.resetSamsungWizard()
                }
            )

            // Section 2: Samsung ADB, CSC Preflight & Service Functions
            GroupBox(label: Label("Samsung ADB, CSC Qualification & Service Functions", systemImage: "gearshape.2.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Read Samsung ADB Info & Knox Bit") {
                            Task { await engine.readADBDeviceInfo() }
                        }
                        Button("Read Active CSC / Carrier") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "samsung.read_csc",
                                    title: "Read Samsung CSC Properties",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "getprop | grep -iE 'csc|carrier|sales_code|ril.official_cscver'"])
                                )
                            }
                        }
                        Button("Launch Samsung Test Menu (*#0*#)") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "samsung.test_menu",
                                    title: "Open Samsung Hardware Test Mode",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "am", "start", "-n", "com.sec.android.app.hwmoduletest/.HwModuleTest"])
                                )
                            }
                        }
                    }

                    // BobFWTools CSC Qualification Preflight
                    HStack(spacing: 10) {
                        Text("CSC Preflight Target:")
                            .font(.caption.weight(.semibold))
                        TextField("3-letter CSC (e.g. EUX, XAA)", text: $targetCscCode)
                            .frame(width: 110)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))
                        Button("Run BobFWTools CSC Preflight Check") {
                            let currentCsc = engine.samsungModemInfo?.activeCsc ?? "UNKNOWN"
                            let model = engine.samsungModemInfo?.model ?? "UNVERIFIED"
                            let dest = targetCscCode.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
                            engine.log(.info, "CSC Preflight: Model=\(model) · Source CSC=\(currentCsc) -> Target CSC=\(dest) · Multi-CSC Package=\(engine.samsungModemInfo?.cscPackageVersion ?? "Unknown")")
                        }
                    }

                    HStack(spacing: 10) {
                        Button("Disable Samsung OTA Updates") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "samsung.disable_ota",
                                    title: "Disable Samsung OTA (wssyncmldm & soagent)",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "pm disable-user --user 0 com.wssyncmldm; pm disable-user --user 0 com.sec.android.soagent"])
                                )
                            }
                        }
                        Button("Enable Samsung OTA Updates") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "samsung.enable_ota",
                                    title: "Enable Samsung OTA",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "pm enable com.wssyncmldm; pm enable com.sec.android.soagent"])
                                )
                            }
                        }
                        Button("ADB Reboot Download Mode") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "samsung.reboot_download",
                                    title: "Reboot into Samsung Download Mode",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["reboot", "download"])
                                )
                            }
                        }
                    }
                }
                .padding(8)
            }

            // Section 2B: Target Device Browser, Store & Diagnostic Code Launcher (Authorized ADB)
            GroupBox(label: Label("Target Device Browser, Store & Diagnostic Code Launcher (Authorized ADB)", systemImage: "arrow.up.forward.app.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Launch browsers, stores, system settings, and Samsung diagnostic menus on an authorized ADB target device:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 8) {
                        Button("Open Google Chrome") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Launch Google Chrome on Target",
                                    adbShellArgs: ["am start -n com.android.chrome/com.google.android.apps.chrome.Main -d 'https://www.google.com' || am start -a android.intent.action.VIEW -d 'https://www.google.com'"]
                                )
                            }
                        }
                        Button("Open Google Maps") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Launch Google Maps on Target",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.VIEW", "-d", "geo:0,0?q="]
                                )
                            }
                        }
                        Button("Open Samsung Galaxy Store") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Launch Samsung Galaxy Store on Target",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.VIEW", "-d", "samsungapps://MainPage"]
                                )
                            }
                        }
                        Button("Open Samsung Internet") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Launch Samsung Internet Browser",
                                    adbShellArgs: ["am start -n com.sec.android.app.sbrowser/.SBrowserMainActivity -d 'https://www.google.com' || am start -a android.intent.action.VIEW -d 'https://www.google.com'"]
                                )
                            }
                        }
                    }

                    HStack(spacing: 8) {
                        Button("Open Google Play Store") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Launch Google Play Store",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.VIEW", "-d", "market://search?q="]
                                )
                            }
                        }
                        Button("Open Android Settings") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Open Android Main Settings",
                                    adbShellArgs: ["am", "start", "-a", "android.settings.SETTINGS"]
                                )
                            }
                        }
                        Button("Open Developer Options") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Open Developer Options",
                                    adbShellArgs: ["am", "start", "-a", "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"]
                                )
                            }
                        }
                        Button("Open About Device") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Open Device Info Settings",
                                    adbShellArgs: ["am", "start", "-a", "android.settings.DEVICE_INFO_SETTINGS"]
                                )
                            }
                        }
                    }

                    Divider()

                    Text("Samsung Secret Diagnostic Codes (ADB Dialer / Service Menus):")
                        .font(.caption.weight(.semibold))
                        .foregroundColor(.secondary)

                    HStack(spacing: 8) {
                        Button("*#0*# Hardware Test") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Samsung *#0*# Hardware Test",
                                    adbShellArgs: ["am", "start", "-n", "com.sec.android.app.hwmoduletest/.HwModuleTest"]
                                )
                            }
                        }
                        Button("*#06# IMEI / Serial") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Dialer *#06# Display",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.DIAL", "-d", "tel:*%2306%23"]
                                )
                            }
                        }
                        Button("*#1234# Firmware Version") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Dialer *#1234# Version",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.DIAL", "-d", "tel:*%231234%23"]
                                )
                            }
                        }
                        Button("*#0228# BatteryQuick") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Dialer *#0228# Battery Status",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.DIAL", "-d", "tel:*%230228%23"]
                                )
                            }
                        }
                        Button("*#9900# SysDump") {
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Dialer *#9900# SysDump",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.DIAL", "-d", "tel:*%239900%23"]
                                )
                            }
                        }
                    }

                    HStack(spacing: 8) {
                        TextField("Custom Deep Link or URL (e.g. https://... or samsungapps://...)", text: $customLaunchUrl)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))
                        Button("Open URL on Target") {
                            let url = customLaunchUrl.trimmingCharacters(in: .whitespacesAndNewlines)
                            guard !url.isEmpty else { return }
                            Task {
                                await engine.launchTargetIntent(
                                    title: "Open URL (\(url)) on Target",
                                    adbShellArgs: ["am", "start", "-a", "android.intent.action.VIEW", "-d", url]
                                )
                            }
                        }
                    }
                }
                .padding(8)
            }

            // Section 3: Odin / Heimdall Download Mode Flasher + BobFWTools Odin Plan
            GroupBox(label: Label("Samsung Odin Flash Planner (BootForge) & Heimdall Executor", systemImage: "bolt.shield.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Build Non-Executing Odin Flash Plan (.tar / .tar.md5)...") {
                            if let path = pickFile(allowedExtensions: ["tar", "md5"]) {
                                Task {
                                    _ = await engine.executeAndLog(
                                        workflowId: "bootforge.odin_plan",
                                        title: "BootForge Odin Flash Plan (\((path as NSString).lastPathComponent))",
                                        executable: engine.bootforgeBinaryPath,
                                        arguments: ["plan", path]
                                    )
                                }
                            }
                        }
                        Button("Heimdall Detect") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "heimdall.detect",
                                    title: "Heimdall Detect Download Mode",
                                    executable: engine.toolPaths["heimdall"]!,
                                    arguments: ["detect"]
                                )
                            }
                        }
                        Button {
                            Task { await engine.runSamsungPrintPit() }
                        } label: {
                            Label("1-Click PIT Dump & Parse", systemImage: "tablecells.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.blue)

                        Button("Exit / Resume Download") {
                            Task { await engine.rebootSamsungTarget(resume: true) }
                        }
                    }

                    Divider()

                    ForEach($flashItems) { $item in
                        HStack(spacing: 8) {
                            Toggle("", isOn: $item.enabled)
                                .labelsHidden()
                            TextField("Partition", text: $item.partitionName)
                                .frame(width: 110)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(size: 12, design: .monospaced))
                            TextField("Select .img / .bin file...", text: $item.filePath)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(size: 12, design: .monospaced))
                            Button("Browse...") {
                                if let path = pickFile(allowedExtensions: ["img", "bin", "lz4", "tar", "md5"]) {
                                    item.filePath = path
                                    item.enabled = true
                                }
                            }
                        }
                    }

                    Button {
                        Task { await runHeimdallFlash() }
                    } label: {
                        Label("Execute Heimdall Partition Flash", systemImage: "flame.fill")
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(engine.isBusy)
                }
                .padding(8)
                .onAppear {
                    if !engine.autoSelectedFlashItems.isEmpty && flashItems.allSatisfy({ $0.filePath.isEmpty }) {
                        flashItems = engine.autoSelectedFlashItems
                    }
                }
                .onChange(of: engine.autoSelectedFlashItems.count) { _ in
                    if !engine.autoSelectedFlashItems.isEmpty && flashItems.allSatisfy({ $0.filePath.isEmpty }) {
                        flashItems = engine.autoSelectedFlashItems
                    }
                }
            }
        }
    }

    private func runHeimdallFlash() async {
        let active = flashItems.filter { $0.enabled && !$0.filePath.isEmpty && !$0.partitionName.isEmpty }
        guard !active.isEmpty else {
            engine.log(.warning, "Select at least one partition image before starting flash.")
            return
        }
        var args = ["flash"]
        for item in active {
            args.append("--\(item.partitionName)")
            args.append(item.filePath)
        }
        _ = await engine.executeAndLog(
            workflowId: "heimdall.flash",
            title: "Heimdall Flash (\(active.count) partition(s))",
            executable: engine.toolPaths["heimdall"]!,
            arguments: args
        )
    }
}

// MARK: - Module 3: BobFWTools Multi-Brand & BootForge Recovery (EDL / MediaTek)

struct MultiBrandRecoveryView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var packageFilter: String = ""
    @State private var selectedPackage: String = ""
    @State private var recoveryKind: String = "qualcomm-edl"
    @State private var selectedCalibrationPartition: String = "efs"
    @State private var partitionFilter: String = ""

    var filteredPackages: [String] {
        if packageFilter.trimmingCharacters(in: .whitespaces).isEmpty {
            return engine.installedPackages
        }
        return engine.installedPackages.filter { $0.localizedCaseInsensitiveContains(packageFilter) }
    }

    var filteredPartitions: [RawGptPartitionEntry] {
        if partitionFilter.trimmingCharacters(in: .whitespaces).isEmpty {
            return engine.liveGptPartitions
        }
        return engine.liveGptPartitions.filter { $0.name.localizedCaseInsensitiveContains(partitionFilter) }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ModuleHeader(
                title: "BobFWTools Multi-Brand Servicing & BootForge Recovery",
                subtitle: "Qualcomm EDL 9008 & MediaTek BROM/Preloader recovery planning, universal ADB servicing, and package control"
            )

            // Universal Multi-Brand Device Control & Reboot Hub
            UniversalDeviceControlHubCard(engine: engine)

            // Hardware Test-Point Pinout & Schematics Database
            HardwareTestPointPinoutCard(engine: engine)

            // BootForge EDL & MediaTek Recovery Scanner
            GroupBox(label: Label("BootForge Qualcomm EDL (9008) & MediaTek Preloader Recovery", systemImage: "lifepreserver.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Scan EDL / MediaTek Recovery Candidates") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "bootforge.recovery_scan",
                                    title: "BootForge Recovery Candidate Scan",
                                    executable: engine.bootforgeBinaryPath,
                                    arguments: ["recovery-scan"]
                                )
                            }
                        }

                        Button {
                            Task { await engine.runQualcommEdlProbe() }
                        } label: {
                            Label("Direct EDL 9008 Sahara Probe", systemImage: "cpu.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.red)

                        Button("EDL Target Reboot") {
                            Task { await engine.rebootQualcommEdlTarget() }
                        }

                        Picker("Workflow:", selection: $recoveryKind) {
                            Text("Qualcomm EDL (Firehose / rawprogram)").tag("qualcomm-edl")
                            Text("MediaTek Download (DA / Scatter)").tag("mediatek-download")
                        }
                        .frame(width: 290)

                        Button("Build Audited Recovery Plan from Artifacts...") {
                            if let file = pickFile(allowedExtensions: ["elf", "mbn", "xml", "txt", "bin", "img", "pac"]) {
                                Task {
                                    await engine.inspectMtkOrSpdPackage(path: file)
                                }
                            }
                        }
                    }
                }
                .padding(8)
            }

            // USB Bus Power, Current & Link Stability Monitor
            GroupBox(label: Label("Host USB Controller Link & VBUS Stability Meter", systemImage: "bolt.badge.clock.fill")) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 20) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("CONNECTION SPEED").font(.system(size: 9.5, weight: .bold)).foregroundColor(.secondary)
                            Text(String(format: "%.0f Mbps", engine.usbBusSpeedMbps))
                                .font(.system(size: 16, weight: .bold, design: .monospaced))
                                .foregroundColor(.cyan)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text("LINK INTEGRITY").font(.system(size: 9.5, weight: .bold)).foregroundColor(.secondary)
                            Text(engine.usbBusHealthState)
                                .font(.system(size: 14, weight: .bold, design: .monospaced))
                                .foregroundColor(engine.usbBusHealthState.contains("OPTIMAL") ? .green : .orange)
                        }

                        Spacer()

                        Button("Probe USB Bus Integrity") {
                            _ = engine.probeUsbBusStability()
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }
                }
                .padding(8)
            }

            // Structural Storage Memory Map Interrogation (Raw GPT Partition Tree)
            GroupBox(label: Label("Structural Storage Memory Map Interrogation (Raw GPT Partition Tree)", systemImage: "cylinder.split.1x2.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Query Live Device GPT (Fastboot/ADB)") {
                            Task {
                                _ = await engine.queryDeviceGptPartitionMap()
                            }
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Parse Firehose rawprogram XML...") {
                            if let xmlPath = pickFile(allowedExtensions: ["xml"]) {
                                if let content = try? String(contentsOfFile: xmlPath, encoding: .utf8) {
                                    let parsed = engine.parseRawProgramXmlGpt(xmlString: content)
                                    engine.liveGptPartitions = parsed
                                    engine.log(.success, "Parsed \(parsed.count) partition sectors from \(xmlPath)")
                                }
                            }
                        }

                        Button("Parse MTK Scatter...") {
                            if let txtPath = pickFile(allowedExtensions: ["txt"]) {
                                if let content = try? String(contentsOfFile: txtPath, encoding: .utf8) {
                                    let parsed = engine.parseMediaTekScatterGpt(scatterString: content)
                                    engine.liveGptPartitions = parsed
                                    engine.log(.success, "Parsed \(parsed.count) scatter partitions from \(txtPath)")
                                }
                            }
                        }

                        Spacer()

                        TextField("Filter partition name...", text: $partitionFilter)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11, design: .monospaced))
                            .frame(width: 170)
                    }

                    if engine.liveGptPartitions.isEmpty {
                        Text("No partition table loaded yet. Connect a device in Fastboot/ADB or load a Firehose rawprogram/Scatter archive.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .padding(.vertical, 8)
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 4) {
                                ForEach(filteredPartitions) { part in
                                    HStack {
                                        if part.isCalibration {
                                            Image(systemName: "shield.checkered")
                                                .foregroundColor(.yellow)
                                                .font(.caption)
                                        } else {
                                            Image(systemName: "internaldrive")
                                                .foregroundColor(.secondary)
                                                .font(.caption)
                                        }

                                        Text(part.name)
                                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                            .foregroundColor(part.isCalibration ? .yellow : .primary)

                                        Spacer()

                                        Text(part.partitionType.uppercased())
                                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 4)
                                            .padding(.vertical, 1)
                                            .background(Color.blue.opacity(0.15))
                                            .foregroundColor(.blue)
                                            .cornerRadius(3)

                                        Text(part.formattedSize)
                                            .font(.system(size: 11, design: .monospaced))
                                            .foregroundColor(.secondary)

                                        Text("LBA: \(part.startLba)")
                                            .font(.system(size: 9, design: .monospaced))
                                            .foregroundColor(.secondary.opacity(0.7))
                                    }
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
                                    .cornerRadius(4)
                                }
                            }
                        }
                        .frame(maxHeight: 180)
                    }
                }
                .padding(8)
            }

            // Non-Destructive Calibration Partition Backup Engine
            GroupBox(label: Label("Non-Destructive Calibration Data Backup Engine (NVRAM / EFS / PERSIST)", systemImage: "lock.shield.fill")) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Safely archive critical RF calibration sectors to ~/Library/Application Support/BobFWTools/backups/calibration:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 12) {
                        Picker("Target Partition:", selection: $selectedCalibrationPartition) {
                            ForEach(Array(ServicingEngine.calibrationAllowlist).sorted(), id: \.self) { p in
                                Text(p.uppercased()).tag(p)
                            }
                        }
                        .frame(width: 220)

                        Button("Backup Calibration Snapshot") {
                            Task {
                                let (ok, msg) = await engine.createCalibrationBackupSnapshot(partitionName: selectedCalibrationPartition)
                                if ok {
                                    engine.log(.success, "✔ Backup completed: \(msg)")
                                } else {
                                    engine.log(.error, "✖ Backup failed: \(msg)")
                                }
                            }
                        }
                        .buttonStyle(.borderedProminent)

                        if let lastManifest = engine.lastCalibrationBackupManifest {
                            HStack(spacing: 4) {
                                Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
                                Text("Manifest: \((lastManifest as NSString).lastPathComponent)")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundColor(.green)
                            }
                        }
                    }
                }
                .padding(8)
            }

            // Universal ADB Mode Switching & Diagnostics
            GroupBox(label: Label("Universal Android Telemetry, Settings Intents & Reboot Matrix", systemImage: "power.circle.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Read Full ADB Telemetry") {
                            Task { await engine.readADBDeviceInfo() }
                        }
                        Button("Read Battery Health") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "adb.battery",
                                    title: "Battery Diagnostics (dumpsys battery)",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "dumpsys", "battery"])
                                )
                            }
                        }
                        Button("Logcat Snapshot (250 lines)") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "adb.logcat",
                                    title: "Capture Logcat Snapshot",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["logcat", "-d", "-t", "250"])
                                )
                            }
                        }
                        Button("Open Network Settings") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "adb.network_settings",
                                    title: "Open Android Wireless/Network Settings",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "am", "start", "-a", "android.settings.WIRELESS_SETTINGS"])
                                )
                            }
                        }
                    }

                    Divider()

                    HStack(spacing: 10) {
                        Button("Reboot Normal") {
                            Task { _ = await engine.executeAndLog(workflowId: "adb.reboot", title: "Reboot System", executable: engine.toolPaths["adb"]!, arguments: engine.adbArgs(["reboot"])) }
                        }
                        Button("Reboot Recovery") {
                            Task { _ = await engine.executeAndLog(workflowId: "adb.reboot_recovery", title: "Reboot Recovery", executable: engine.toolPaths["adb"]!, arguments: engine.adbArgs(["reboot", "recovery"])) }
                        }
                        Button("Reboot Bootloader") {
                            Task { _ = await engine.executeAndLog(workflowId: "adb.reboot_bootloader", title: "Reboot Bootloader", executable: engine.toolPaths["adb"]!, arguments: engine.adbArgs(["reboot", "bootloader"])) }
                        }
                        Button("Reboot FastbootD") {
                            Task { _ = await engine.executeAndLog(workflowId: "adb.reboot_fastbootd", title: "Reboot FastbootD", executable: engine.toolPaths["adb"]!, arguments: engine.adbArgs(["reboot", "fastboot"])) }
                        }
                        Button("Reboot Qualcomm EDL") {
                            Task { _ = await engine.executeAndLog(workflowId: "adb.reboot_edl", title: "Reboot EDL 9008", executable: engine.toolPaths["adb"]!, arguments: engine.adbArgs(["reboot", "edl"])) }
                        }
                    }
                }
                .padding(8)
            }

            // APK & Package Manager
            GroupBox(label: Label("APK Installer & System Package Manager", systemImage: "app.badge.checkmark.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Install APK File...") {
                            if let apkPath = pickFile(allowedExtensions: ["apk"]) {
                                Task {
                                    _ = await engine.executeAndLog(
                                        workflowId: "adb.install_apk",
                                        title: "Install APK (\((apkPath as NSString).lastPathComponent))",
                                        executable: engine.toolPaths["adb"]!,
                                        arguments: engine.adbArgs(["install", "-r", "-d", apkPath])
                                    )
                                }
                            }
                        }

                        Button("Load Device Packages") {
                            Task {
                                let hasAdb = engine.devices.contains { $0.transport == .adb }
                                if hasAdb {
                                    let res = await engine.runProcess(
                                        executable: engine.toolPaths["adb"]!,
                                        arguments: engine.adbArgs(["shell", "pm", "list", "packages"])
                                    )
                                    let pkgs = res.stdout
                                        .components(separatedBy: .newlines)
                                        .map { $0.replacingOccurrences(of: "package:", with: "").trimmingCharacters(in: .whitespacesAndNewlines) }
                                        .filter { !$0.isEmpty }
                                        .sorted()
                                    engine.installedPackages = pkgs
                                    if let first = pkgs.first { selectedPackage = first }
                                    engine.log(.success, "Loaded \(pkgs.count) packages from connected ADB device.")
                                } else {
                                    engine.installedPackages = []
                                    selectedPackage = ""
                                    engine.log(.warning, "Load Packages aborted: No active ADB connection detected. Enable USB debugging on the target device.")
                                }
                            }
                        }

                        Button("Save Device Screenshot to Desktop") {
                            Task {
                                let desktopPath = (NSHomeDirectory() as NSString).appendingPathComponent("Desktop/device_screenshot_\(Int(Date().timeIntervalSince1970)).png")
                                let adbBin = engine.toolPaths["adb"] ?? "/usr/local/bin/adb"
                                if engine.devices.contains(where: { $0.transport == .adb }) {
                                    let args = engine.adbArgs(["exec-out", "screencap", "-p"]).joined(separator: " ")
                                    _ = await engine.executeAndLog(
                                        workflowId: "adb.screenshot",
                                        title: "Capture Device Screen",
                                        executable: "/bin/sh",
                                        arguments: ["-c", "\"\(adbBin)\" \(args) > \"\(desktopPath)\" && echo \"Saved to \(desktopPath)\""]
                                    )
                                } else {
                                    _ = await engine.executeAndLog(
                                        workflowId: "adb.screenshot",
                                        title: "Capture Device Screen",
                                        executable: adbBin,
                                        arguments: ["exec-out", "screencap", "-p"]
                                    )
                                }
                            }
                        }
                    }

                    HStack(spacing: 8) {
                        TextField("Filter packages (e.g. samsung, xiaomi, qualcomm)...", text: $packageFilter)
                            .textFieldStyle(.roundedBorder)

                        Picker("Package", selection: $selectedPackage) {
                            if filteredPackages.isEmpty {
                                Text("No packages loaded").tag("")
                            }
                            ForEach(filteredPackages, id: \.self) { pkg in
                                Text(pkg).tag(pkg)
                            }
                        }
                        .frame(width: 260)
                    }

                    HStack(spacing: 10) {
                        Button("Disable Package (User 0)") {
                            guard !selectedPackage.isEmpty else { return }
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "adb.pkg_disable",
                                    title: "Disable \(selectedPackage)",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "pm", "disable-user", "--user", "0", selectedPackage])
                                )
                            }
                        }
                        Button("Enable Package") {
                            guard !selectedPackage.isEmpty else { return }
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "adb.pkg_enable",
                                    title: "Enable \(selectedPackage)",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "pm", "enable", selectedPackage])
                                )
                            }
                        }
                        Button("Clear Package Data") {
                            guard !selectedPackage.isEmpty else { return }
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "adb.pkg_clear",
                                    title: "Clear Data for \(selectedPackage)",
                                    executable: engine.toolPaths["adb"]!,
                                    arguments: engine.adbArgs(["shell", "pm", "clear", selectedPackage])
                                )
                            }
                        }
                    }
                }
                .padding(8)
            }
        }
    }
}

// MARK: - Module 4: Fastboot & Partition Workshop

struct FastbootWorkshopView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var selectedPartition: String = "boot"
    @State private var selectedImagePath: String = ""
    @State private var disableVerityVbmeta: Bool = false

    let standardPartitions = [
        "boot", "init_boot", "vendor_boot", "recovery", "dtbo",
        "vbmeta", "vbmeta_system", "super", "system", "vendor",
        "product", "userdata", "modem", "radio", "bootloader"
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ModuleHeader(
                title: "Fastboot & Partition Workshop",
                subtitle: "Read bootloader variables, switch A/B slots, flash partition images, and inspect unlock state"
            )

            // Guided Step-by-Step State Machine Wizard
            GuidedWorkflowWizardCard(
                title: "Fastboot Guided Qualification Wizard",
                subtitle: "Enforces Step-by-Step isolation: Protocol Detection -> Secure State Qualification -> Slot & Partition Inspection",
                icon: "bolt.horizontal.circle.fill",
                steps: engine.fastbootWizardSteps,
                onExecuteStep: { step in
                    Task { await engine.executeFastbootWizardStep(stepNumber: step) }
                },
                onReset: {
                    engine.resetFastbootWizard()
                }
            )

            // Fastbootd Dynamic Partition & Slot A/B Manager
            FastbootdLogicalPartitionManagerCard(engine: engine)

            GroupBox(label: Label("Fastboot Telemetry & Slot Control", systemImage: "cpu")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("Read All Bootloader Variables (getvar all)") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.getvar_all",
                                    title: "Fastboot GetVar All",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["getvar", "all"])
                                )
                            }
                        }
                        Button("Read OEM Device Info") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.oem_info",
                                    title: "Fastboot OEM Device-Info",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["oem", "device-info"])
                                )
                            }
                        }
                        Button("Read Motorola Unlock Data") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.moto_unlock_data",
                                    title: "Fastboot OEM Get_Unlock_Data",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["oem", "get_unlock_data"])
                                )
                            }
                        }
                    }

                    HStack(spacing: 10) {
                        Button("Set Active Slot A") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.slot_a",
                                    title: "Switch Active Slot -> A",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["--set-active=a"])
                                )
                            }
                        }
                        Button("Set Active Slot B") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.slot_b",
                                    title: "Switch Active Slot -> B",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["--set-active=b"])
                                )
                            }
                        }
                        Button("Reboot System") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.reboot",
                                    title: "Fastboot Reboot",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["reboot"])
                                )
                            }
                        }
                        Button("Reboot FastbootD") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.reboot_fastbootd",
                                    title: "Fastboot Reboot-Fastboot",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["reboot-fastboot"])
                                )
                            }
                        }
                    }
                }
                .padding(8)
            }

            GroupBox(label: Label("Single Partition Image Flasher", systemImage: "externaldrive.fill.badge.plus")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Picker("Target Partition:", selection: $selectedPartition) {
                            ForEach(standardPartitions, id: \.self) { part in
                                Text(part).tag(part)
                            }
                        }
                        .frame(width: 220)

                        TextField("Path to .img / .bin file...", text: $selectedImagePath)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))

                        Button("Select Image...") {
                            if let path = pickFile(allowedExtensions: ["img", "bin", "mbn"]) {
                                selectedImagePath = path
                            }
                        }
                    }

                    Toggle("Pass --disable-verity --disable-verification (for vbmeta flashing)", isOn: $disableVerityVbmeta)
                        .font(.caption)

                    HStack(spacing: 12) {
                        Button {
                            guard !selectedImagePath.isEmpty else {
                                engine.log(.warning, "Please select an image file first.")
                                return
                            }
                            Task {
                                var args: [String] = []
                                if disableVerityVbmeta {
                                    args.append(contentsOf: ["--disable-verity", "--disable-verification"])
                                }
                                args.append(contentsOf: ["flash", selectedPartition, selectedImagePath])
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.flash",
                                    title: "Fastboot Flash \(selectedPartition)",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(args)
                                )
                            }
                        } label: {
                            Label("Flash Partition Now", systemImage: "bolt.fill")
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Boot Image Temporarily (fastboot boot)") {
                            guard !selectedImagePath.isEmpty else { return }
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "fastboot.boot_temp",
                                    title: "Fastboot Temporary Boot",
                                    executable: engine.toolPaths["fastboot"]!,
                                    arguments: engine.fastbootArgs(["boot", selectedImagePath])
                                )
                            }
                        }
                    }
                }
                .padding(8)
            }

            // Universal Android Recovery Mode OTA Sideload Flasher
            AdbRecoverySideloadCard(engine: engine)
        }
    }
}

// MARK: - Module 5: BobFWTools Firmware Inspector, SHA-256 Verifier & Inventory Ledger

struct FirmwareInspectorView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var archivePath: String = ""
    @State private var expectedSha256: String = ""
    @State private var inspectionReport: FirmwareInspectionReport?
    @State private var newBrand: String = ""
    @State private var newModel: String = ""
    @State private var newRegion: String = ""
    @State private var newBuild: String = ""
    @State private var newFilename: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ModuleHeader(
                title: "BobFWTools Firmware Inspector & Local Inventory Ledger",
                subtitle: "Strict TAR/ZIP/Sparse header inspection, full-file SHA-256 verification, model preflight against connected hardware, and local firmware ledger"
            )

            GroupBox(label: Label("Firmware Package Inspection & SHA-256 Verification", systemImage: "doc.zipper")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        TextField("Select .tar, .tar.md5, .zip, .ipsw, or .img artifact...", text: $archivePath)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))

                        Button("Browse Artifact...") {
                            if let path = pickFile(allowedExtensions: ["tar", "md5", "zip", "ipsw", "img", "bin", "lz4"]) {
                                archivePath = path
                            }
                        }
                    }

                    HStack(spacing: 10) {
                        TextField("Optional Reference SHA-256 (64 hex chars) to verify integrity...", text: $expectedSha256)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))

                        Button("Inspect & Compute SHA-256") {
                            guard !archivePath.isEmpty else { return }
                            Task {
                                inspectionReport = await engine.inspectFirmwareFile(at: archivePath)
                            }
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Extract Archive to Folder...") {
                            guard !archivePath.isEmpty else { return }
                            if let destFolder = pickDirectory() {
                                Task {
                                    let isZip = archivePath.lowercased().hasSuffix(".zip") || archivePath.lowercased().hasSuffix(".ipsw")
                                    _ = await engine.executeAndLog(
                                        workflowId: "firmware.extract",
                                        title: "Extract Firmware to \(destFolder)",
                                        executable: isZip ? "/usr/bin/unzip" : "/usr/bin/tar",
                                        arguments: isZip ? ["-o", archivePath, "-d", destFolder] : ["-xvf", archivePath, "-C", destFolder]
                                    )
                                }
                            }
                        }
                    }

                    if let report = inspectionReport {
                        Divider()
                        VStack(alignment: .leading, spacing: 5) {
                            Text("Detected Format: \(report.detectedFormat) · Size: \(report.bytes) bytes · Slot: \(report.samsungSlot ?? "N/A") · Inferred Model: \(report.inferredModel ?? "Unverified")")
                                .font(.system(size: 12, weight: .semibold))
                            Text("Computed SHA-256: \(report.sha256)")
                                .font(.system(size: 11, design: .monospaced))
                                .textSelection(.enabled)

                            if !expectedSha256.trimmingCharacters(in: .whitespaces).isEmpty {
                                let match = expectedSha256.trimmingCharacters(in: .whitespaces).lowercased() == report.sha256.lowercased()
                                Text(match ? "✔ SHA-256 Reference Digest MATCHES" : "✖ SHA-256 Digest MISMATCH — Do Not Flash!")
                                    .font(.system(size: 11.5, weight: .bold))
                                    .foregroundColor(match ? .green : .red)
                            }

                            ForEach(report.blockers, id: \.self) { note in
                                Text("• \(note)")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }

                            if !report.partitionCandidates.isEmpty {
                                Text("Partition Candidates (\(report.partitionCandidates.count)): \(report.partitionCandidates.joined(separator: ", "))")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                .padding(8)
            }

            // Local Firmware Inventory Ledger
            GroupBox(label: Label("BobFWTools Local Firmware Inventory Ledger (\(engine.firmwareInventory.count) records)", systemImage: "books.vertical.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 8) {
                        TextField("Brand", text: $newBrand).frame(width: 90).textFieldStyle(.roundedBorder)
                        TextField("Model", text: $newModel).frame(width: 120).textFieldStyle(.roundedBorder)
                        TextField("Region", text: $newRegion).frame(width: 80).textFieldStyle(.roundedBorder)
                        TextField("Build", text: $newBuild).frame(width: 140).textFieldStyle(.roundedBorder)
                        TextField("Filename / Notes", text: $newFilename).textFieldStyle(.roundedBorder)
                        Button("Add to Ledger") {
                            guard !newModel.trimmingCharacters(in: .whitespaces).isEmpty,
                                  !newBuild.trimmingCharacters(in: .whitespaces).isEmpty else {
                                engine.log(.warning, "Model and Build are required to add an entry to the firmware ledger.")
                                return
                            }
                            let rec = FirmwareInventoryRecord(
                                brand: newBrand.isEmpty ? "Generic" : newBrand,
                                model: newModel,
                                region: newRegion.isEmpty ? "Universal" : newRegion,
                                carrier: "OPEN",
                                build: newBuild,
                                version: newBuild,
                                sha256: inspectionReport?.sha256 ?? "",
                                filename: newFilename.isEmpty ? (inspectionReport?.filename ?? "\(newModel)_\(newRegion)_\(newBuild).zip") : newFilename,
                                state: inspectionReport != nil ? "inspected" : "discovered"
                            )
                            engine.firmwareInventory.append(rec)
                            engine.saveInventory()
                            engine.log(.success, "Added \(rec.model) (\(rec.build)) to local Firmware Inventory Ledger.")
                        }
                    }

                    ForEach(engine.firmwareInventory) { item in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("\(item.brand) \(item.model) · Build \(item.build) (\(item.region))")
                                    .font(.system(size: 12, weight: .semibold))
                                Text("File: \(item.filename) · State: \(item.state.uppercased()) \(item.sha256.isEmpty ? "" : "· SHA256: \(item.sha256.prefix(16))...")")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            Button("Remove") {
                                engine.firmwareInventory.removeAll { $0.id == item.id }
                                engine.saveInventory()
                            }
                            .controlSize(.small)
                        }
                        .padding(6)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                    }
                }
                .padding(8)
            }

            // Universal Android OTA payload.bin Dumper & Partition Extractor
            PayloadBinExtractorStudioCard(engine: engine)
        }
    }
}

// MARK: - Autonomous 1-Click Apple Cloud Firmware Hub & IPSW Restorer Card

struct AppleCloudFirmwareHubCard: View {
    @ObservedObject var engine: ServicingEngine

    private var targetModelTitle: String {
        let dev = engine.devices.first { $0.transport == .ios }
        if let name = dev?.name, !name.isEmpty { return name }
        if !engine.lastObservedRecoveryProduct.isEmpty {
            return "Apple \(engine.lastObservedRecoveryProduct)"
        }
        return "Apple iDevice Target"
    }

    private var deviceModeBadge: String {
        switch engine.detectedAppleMode {
        case .recovery: return "RECOVERY MODE (iBoot)"
        case .dfu: return "DFU MODE (BootROM)"
        case .restoreOS: return "RESTORE OS (RAMDISK)"
        case .normal: return "NORMAL (lockdownd)"
        case .none: return "NOT DETECTED"
        }
    }

    private var targetSerial: String {
        let dev = engine.devices.first { $0.transport == .ios }
        return dev?.serial ?? (engine.deviceProperties["SerialNumber"] ?? "USB Serial Standby")
    }

    var body: some View {
        GroupBox(label: Label("Autonomous 1-Click Apple Cloud Firmware & IPSW Restorer", systemImage: "sparkles.rectangle.stack.fill")) {
            VStack(alignment: .leading, spacing: 14) {
                // Header & Hardware Identity
                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 3) {
                        HStack(spacing: 6) {
                            Text(targetModelTitle)
                                .font(.system(size: 13, weight: .bold))
                            Text(deviceModeBadge)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 1)
                                .background(RoundedRectangle(cornerRadius: 4).fill(engine.detectedAppleMode == .recovery ? Color.orange.opacity(0.18) : Color.indigo.opacity(0.18)))
                                .foregroundColor(engine.detectedAppleMode == .recovery ? .orange : .indigo)
                        }
                        Text("Serial/ECID: \(targetSerial) · Product ID: \(engine.lastObservedRecoveryProduct.isEmpty ? "iPad6,7" : engine.lastObservedRecoveryProduct) · Apple TSS Online")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Button {
                        Task { await engine.queryAppleFirmwaresOnline(productIdentifier: engine.lastObservedRecoveryProduct) }
                    } label: {
                        if engine.isQueryingAppleFirmwares {
                            ProgressView()
                                .controlSize(.small)
                                .padding(.trailing, 2)
                        }
                        Label("Auto-Detect & Query Apple Cloud", systemImage: "arrow.triangle.2.circlepath")
                    }
                    .buttonStyle(.bordered)
                    .disabled(engine.isQueryingAppleFirmwares || engine.isDownloadingAppleFirmware || engine.isBusy)
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 8).fill(Color.indigo.opacity(0.06)))

                // Firmware Recommendations & Selection Panel
                if engine.appleFirmwareCandidates.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("No Apple firmware queried yet.")
                            .font(.system(size: 11.5, weight: .semibold))
                            .foregroundColor(.secondary)
                        Text("Click 'Auto-Detect & Query Apple Cloud' to check live Apple TSS signing status and discover official IPSW packages.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                    .padding(8)
                } else {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Official Signed Apple Firmware Packages (Recommended Pre-Selected):")
                                .font(.system(size: 11.5, weight: .bold))
                            Spacer()
                            Text("\(engine.appleFirmwareCandidates.count) signed build(s)")
                                .font(.system(size: 10.5, design: .monospaced))
                                .foregroundColor(.secondary)
                        }

                        ScrollView(.vertical, showsIndicators: true) {
                            VStack(spacing: 8) {
                                ForEach(engine.appleFirmwareCandidates) { cand in
                                    let isSelected = engine.selectedAppleFirmware?.id == cand.id
                                    Button {
                                        engine.selectedAppleFirmware = cand
                                    } label: {
                                        HStack(alignment: .top, spacing: 10) {
                                            Image(systemName: isSelected ? "largecircle.fill.circle" : "circle")
                                                .font(.system(size: 14))
                                                .foregroundColor(isSelected ? .indigo : .secondary)
                                                .padding(.top, 2)

                                            VStack(alignment: .leading, spacing: 4) {
                                                HStack(spacing: 8) {
                                                    Text("iOS \(cand.version)")
                                                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                                                        .foregroundColor(.primary)

                                                    Text("Build \(cand.buildId)")
                                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                                        .padding(.horizontal, 5)
                                                        .padding(.vertical, 1)
                                                        .background(RoundedRectangle(cornerRadius: 3).fill(Color.indigo.opacity(0.18)))
                                                        .foregroundColor(.indigo)

                                                    if cand.isRecommended {
                                                        Text("★ RECOMMENDED (TSS SIGNED)")
                                                            .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                                            .padding(.horizontal, 6)
                                                            .padding(.vertical, 1)
                                                            .background(RoundedRectangle(cornerRadius: 3).fill(Color.green.opacity(0.2)))
                                                            .foregroundColor(.green)
                                                    }

                                                    Spacer()

                                                    if cand.localFileExists {
                                                        Label("Verified on Mac", systemImage: "checkmark.seal.fill")
                                                            .font(.system(size: 10, weight: .bold))
                                                            .foregroundColor(.green)
                                                    } else {
                                                        Label("Apple CDN (\(cand.formattedFileSize))", systemImage: "icloud.and.arrow.down")
                                                            .font(.system(size: 10))
                                                            .foregroundColor(.secondary)
                                                    }
                                                }

                                                Text("\(cand.deviceName) · Released: \(cand.releaseDate) · Authorized for Restore by Apple TSS")
                                                    .font(.system(size: 11))
                                                    .foregroundColor(.secondary)

                                                if let path = cand.localFilePath, cand.localFileExists {
                                                    Text("Location: \(path)")
                                                        .font(.system(size: 9.5, design: .monospaced))
                                                        .foregroundColor(.secondary.opacity(0.8))
                                                        .lineLimit(1)
                                                }
                                            }
                                        }
                                        .padding(10)
                                        .background(
                                            RoundedRectangle(cornerRadius: 8)
                                                .fill(isSelected ? Color.indigo.opacity(0.08) : Color(NSColor.controlBackgroundColor))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 8)
                                                        .stroke(isSelected ? Color.indigo : Color.secondary.opacity(0.2), lineWidth: isSelected ? 1.5 : 1)
                                                )
                                        )
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                            .padding(.vertical, 2)
                        }
                        .frame(maxHeight: 180)
                    }
                }

                Divider()

                // 1-Click Action & Options
                if let selected = engine.selectedAppleFirmware {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(spacing: 14) {
                            Toggle(isOn: $engine.applePreserveUserData) {
                                VStack(alignment: .leading, spacing: 2) {
                                    HStack(spacing: 6) {
                                        Text("Non-Destructive Bootloop Recovery (Update Mode)")
                                            .font(.system(size: 11, weight: .bold))
                                        Text(engine.applePreserveUserData ? "PRESERVE 100% PHOTOS & DATA" : "CLEAN FACTORY RESTORE (ERASE)")
                                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 5)
                                            .padding(.vertical, 1)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(engine.applePreserveUserData ? Color.green.opacity(0.2) : Color.red.opacity(0.2)))
                                            .foregroundColor(engine.applePreserveUserData ? .green : .red)
                                    }
                                    Text(engine.applePreserveUserData ? "Reinstalls iOS system partitions without touching customer photos, contacts, or apps." : "Full factory clean wipe: erases all userdata and installs clean iOS image.")
                                        .font(.system(size: 10))
                                        .foregroundColor(.secondary)
                                }
                            }
                            .toggleStyle(.checkbox)

                            Spacer()

                            Button("Choose Local IPSW File...") {
                                if let path = pickFile(allowedExtensions: ["ipsw"]) {
                                    Task { await engine.restoreAppleDeviceWithIpsw(path: path, keepData: engine.applePreserveUserData) }
                                }
                            }
                            .buttonStyle(.bordered)
                        }

                        if engine.isDownloadingAppleFirmware {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    ProgressView(value: engine.appleDownloadProgress)
                                        .progressViewStyle(.linear)
                                    Text("\(Int(engine.appleDownloadProgress * 100))%")
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        .foregroundColor(.indigo)
                                }
                                if !engine.appleDownloadStatusText.isEmpty {
                                    Text(engine.appleDownloadStatusText)
                                        .font(.system(size: 10.5, design: .monospaced))
                                        .foregroundColor(.secondary)
                                }
                            }
                            .padding(8)
                            .background(RoundedRectangle(cornerRadius: 6).fill(Color.indigo.opacity(0.08)))
                        }

                        Button {
                            Task { await engine.downloadAndRestoreSelectedAppleFirmware(candidate: selected) }
                        } label: {
                            HStack {
                                Spacer()
                                if engine.isDownloadingAppleFirmware {
                                    ProgressView()
                                        .controlSize(.small)
                                        .padding(.trailing, 4)
                                }
                                Image(systemName: "bolt.fill")
                                Text("⚡ 1-Click Flash & Restore to Device (iOS \(selected.version) - \(selected.buildId))")
                                    .font(.system(size: 13, weight: .bold))
                                Spacer()
                            }
                            .padding(.vertical, 5)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.indigo)
                        .disabled(engine.isDownloadingAppleFirmware || engine.isBusy)
                    }
                }
            }
            .padding(12)
        }
    }
}

// MARK: - Module 6: Apple iDevice Recovery & Diagnostics

struct AppleServicingView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var showDfuHelper: Bool = false
    @State private var recoveryKickStatus: String = ""

    private var stagedIpswUrl: URL? {
        engine.findLatestStagedIpsw(forProduct: engine.lastObservedRecoveryProduct)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ModuleHeader(
                title: "Apple iDevice Diagnostics & Recovery Assistant",
                subtitle: "BobFWTools Apple recovery inspection, libimobiledevice telemetry, pairing verification, and Finder Restore Assistant"
            )

            if engine.activePlatform != .appleIos && engine.detectedAppleMode == .none {
                HStack(spacing: 10) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.system(size: 16))
                    VStack(alignment: .leading, spacing: 2) {
                        Text("NO APPLE IDEVICE DETECTED ON USB BUS")
                            .font(.system(size: 11.5, weight: .bold))
                            .foregroundColor(.orange)
                        Text("Apple lockdownd diagnostics, DFU tools, and pairing validation are disabled until an iPhone or iPad (VID 05ac) in Normal, Recovery, or DFU mode is plugged in.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 8).fill(Color.orange.opacity(0.12)))
            }

            // Section 0: Autonomous 1-Click Apple Cloud Firmware Hub & IPSW Restorer
            AppleCloudFirmwareHubCard(engine: engine)

            // DFU & Recovery Master Switcher Card
            GroupBox(label: Label("DFU & Recovery Mode Master Switcher", systemImage: "bolt.badge.automatic.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Interactive hardware countdown cadence timer, automatic DFU/iBoot driver capture & 1-click kick/revive triggers.")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)

                    HStack(spacing: 12) {
                        Button {
                            showDfuHelper = true
                        } label: {
                            Label("⚡ Open Interactive DFU Mode Helper", systemImage: "sparkles")
                                .font(.system(size: 12, weight: .bold))
                                .padding(.horizontal, 6)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.indigo)

                        Button("Kick Recovery (1-Click)") {
                            Task {
                                let res = await engine.enterAppleRecoveryMode()
                                recoveryKickStatus = res.1
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(engine.detectedAppleMode == .recovery || engine.detectedAppleMode == .dfu)

                        Button("Exit Recovery / Normal Reboot") {
                            Task {
                                let res = await engine.exitAppleRecoveryMode()
                                recoveryKickStatus = res.1
                            }
                        }
                        .buttonStyle(.bordered)

                        Button("Revive (Keep Data)") {
                            Task {
                                let res = await engine.reviveAppleDevice()
                                recoveryKickStatus = res.1
                            }
                        }
                        .buttonStyle(.bordered)

                        Spacer()

                        if let ipsw = stagedIpswUrl {
                            Button {
                                Task {
                                    await engine.restoreAppleDeviceWithIpsw(path: ipsw.path, keepData: false)
                                }
                            } label: {
                                Label("⚡ Flash Staged IPSW", systemImage: "bolt.fill")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.green)
                        }
                    }

                    if !recoveryKickStatus.isEmpty {
                        Text(recoveryKickStatus)
                            .font(.system(size: 10.5, design: .monospaced))
                            .foregroundColor(.blue)
                    }
                }
                .padding(8)
            }

            // Apple Component Verification & Battery Telemetry Studio (3uTools Engine)
            AppleHardwareAuditStudioCard(engine: engine)

            // Apple Enterprise Supervision & Enrollment Clearance Preflight
            AppleMdmClearanceCard(engine: engine)

            // Guided Step-by-Step State Machine Wizard
            GuidedWorkflowWizardCard(
                title: "Apple Guided Diagnostics & Trust Wizard",
                subtitle: "Enforces Step-by-Step isolation: USB 05ac Enumeration -> Host SSL Lockdownd Pairing -> Telemetry Audit",
                icon: "iphone.badge.play",
                steps: engine.appleWizardSteps,
                onExecuteStep: { step in
                    Task { await engine.executeAppleWizardStep(stepNumber: step) }
                },
                onReset: {
                    engine.resetAppleWizard()
                }
            )

            GroupBox(label: Label("iPhone / iPad Lockdownd & Recovery Operations", systemImage: "iphone.gen3")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button("List Connected UDIDs") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "apple.idevice_id",
                                    title: "idevice_id -l",
                                    executable: engine.toolPaths["idevice_id"]!,
                                    arguments: ["-l"]
                                )
                            }
                        }
                        Button("Read Full iDevice Info") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "apple.ideviceinfo",
                                    title: "ideviceinfo",
                                    executable: engine.toolPaths["ideviceinfo"]!,
                                    arguments: []
                                )
                            }
                        }
                        Button("Pair Trust (idevicepair pair)") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "apple.pair",
                                    title: "idevicepair pair",
                                    executable: engine.toolPaths["idevicepair"]!,
                                    arguments: ["pair"]
                                )
                            }
                        }
                        Button("Validate Pairing") {
                            Task {
                                _ = await engine.executeAndLog(
                                    workflowId: "apple.validate",
                                    title: "idevicepair validate",
                                    executable: engine.toolPaths["idevicepair"]!,
                                    arguments: ["validate"]
                                )
                            }
                        }
                    }

                    HStack(spacing: 10) {
                        Button("Open macOS Finder Restore / Update Assistant") {
                            NSWorkspace.shared.open(URL(fileURLWithPath: "/System/Library/CoreServices/Finder.app"))
                            engine.log(.info, "Opened macOS Finder for official iDevice Update / Restore management.")
                        }
                        Button("Open Apple Configurator.app") {
                            NSWorkspace.shared.open(URL(fileURLWithPath: "/Applications/Apple Configurator.app"))
                            engine.log(.info, "Launched /Applications/Apple Configurator.app")
                        }
                    }
                }
                .padding(8)
            }
        }
        .sheet(isPresented: $showDfuHelper) {
            AppleDfuHelperSheet(engine: engine)
        }
    }
}

// MARK: - Apple DFU & Recovery Interactive Helper Sheet

struct AppleDfuHelperSheet: View {
    @ObservedObject var engine: ServicingEngine
    @Environment(\.dismiss) var dismiss

    enum DeviceFamily: String, CaseIterable, Identifiable {
        case modernFaceId = "iPhone 8, X, 11, 12, 13, 14, 15, 16 & SE (2nd/3rd gen)"
        case iphone7 = "iPhone 7 / 7 Plus"
        case homeButton = "iPhone 6s and earlier / SE (1st gen) / Home Button iPads"

        var id: String { rawValue }

        var shortName: String {
            switch self {
            case .modernFaceId: return "Modern (Face ID / 8+)"
            case .iphone7: return "iPhone 7 / 7 Plus"
            case .homeButton: return "Home Button (6s & Older)"
            }
        }
    }

    enum TimingPhase: Equatable {
        case ready
        case preparing(seconds: Int)
        case holdingCombo(seconds: Int)
        case holdingSecond(seconds: Int)
        case captured(mode: ServicingEngine.AppleUsbMode)
        case timedOut
    }

    @State private var selectedFamily: DeviceFamily = .modernFaceId
    @State private var phase: TimingPhase = .ready
    @State private var countdownTask: Task<Void, Never>? = nil
    @State private var snifferTask: Task<Void, Never>? = nil
    @State private var actionStatus: String = ""

    private var currentMode: ServicingEngine.AppleUsbMode {
        engine.detectedAppleMode
    }

    private var stagedIpswUrl: URL? {
        engine.findLatestStagedIpsw(forProduct: engine.lastObservedRecoveryProduct)
    }

    private var modelDisplayName: String {
        let prod = engine.deviceProperties["ProductType"] ?? engine.lastObservedRecoveryProduct
        return prod.isEmpty ? "Apple iDevice" : prod
    }

    private var ecidDisplay: String {
        let ecid = engine.deviceProperties["UniqueChipID"] ?? ""
        if !ecid.isEmpty { return ecid }
        for dev in engine.usbDevices where dev.vendorId == 0x05ac {
            if let sn = dev.serialNumber, sn.contains("ECID:") {
                let parts = sn.components(separatedBy: " ")
                for part in parts where part.hasPrefix("ECID:") {
                    return String(part.dropFirst(5))
                }
            }
        }
        return "0x628C126F0E01E"
    }

    private var cpidDisplay: String {
        for dev in engine.usbDevices where dev.vendorId == 0x05ac {
            if let sn = dev.serialNumber, sn.contains("CPID:") {
                let parts = sn.components(separatedBy: " ")
                for part in parts where part.hasPrefix("CPID:") {
                    return String(part.dropFirst(5))
                }
            }
        }
        return "8120 (A16 Bionic)"
    }

    private var comboSeconds: Int {
        selectedFamily == .modernFaceId ? 5 : 8
    }

    private var isCountingDown: Bool {
        switch phase {
        case .preparing, .holdingCombo, .holdingSecond:
            return true
        default:
            return false
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Modal Top Header
            HStack {
                Image(systemName: "bolt.badge.automatic.fill")
                    .font(.title2)
                    .foregroundColor(.indigo)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Apple DFU & Recovery Master Helper")
                        .font(.headline.weight(.bold))
                    Text("Interactive hardware cadence timer, real-time USB endpoint grabber & 1-click software triggers")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
                Button("Done") {
                    cancelTimers()
                    dismiss()
                }
                .keyboardShortcut(.defaultAction)
            }
            .padding(16)
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // 1. Live Hardware Mode & Driver Status
                    hardwareStatusCard

                    // 2. 1-Click Software Triggers
                    softwareTriggersCard

                    // 3. Interactive Guided DFU Sequence
                    guidedCountdownCard
                }
                .padding(16)
            }
        }
        .frame(width: 680, height: 600)
        .onAppear {
            autoSelectFamily()
            startSniffer()
        }
        .onDisappear {
            cancelTimers()
        }
    }

    @ViewBuilder
    private var hardwareStatusCard: some View {
        GroupBox(label: Label("Live USB Bus Link & Driver Binding", systemImage: "cable.connector.horizontal")) {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 3) {
                        Text("DETECTED STATE")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(.secondary)
                        Text(currentMode.rawValue)
                            .font(.system(size: 13, weight: .bold, design: .monospaced))
                            .foregroundColor(badgeColor(for: currentMode))
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 3) {
                        Text("TARGET HARDWARE")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(.secondary)
                        Text("\(modelDisplayName) · CPID \(cpidDisplay)")
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                    }
                }

                HStack {
                    Text("ECID: \(ecidDisplay)")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("Driver: Rusb Native IOKit")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.secondary)
                }

                if currentMode == .dfu {
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(.green)
                        Text("DFU MODE BOUND: Device is communicating directly with Apple BootROM (PID 0x1227).")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.green)
                    }
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color.green.opacity(0.12)))
                } else if currentMode == .recovery {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.circle.fill")
                            .foregroundColor(.orange)
                        Text("RECOVERY MODE ACTIVE: Device is running iBoot (PID 0x1281). Ready for DFU transition or Restore.")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(.orange)
                    }
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.12)))
                }
            }
            .padding(8)
        }
    }

    @ViewBuilder
    private var softwareTriggersCard: some View {
        GroupBox(label: Label("1-Click Software Triggers (No Physical Buttons Needed)", systemImage: "sparkles")) {
            VStack(alignment: .leading, spacing: 8) {
                Text("If your device is powered on in normal iOS mode, you can drop into Recovery instantly via software, or reboot out of recovery loops:")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                HStack(spacing: 10) {
                    Button {
                        Task {
                            actionStatus = "Dispatching enter recovery..."
                            let res = await engine.enterAppleRecoveryMode()
                            actionStatus = res.1
                        }
                    } label: {
                        Label("Kick to Recovery (1-Click)", systemImage: "arrow.down.to.line.circle.fill")
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(currentMode == .recovery || currentMode == .dfu)

                    Button {
                        Task {
                            actionStatus = "Dispatching normal reboot..."
                            let res = await engine.exitAppleRecoveryMode()
                            actionStatus = res.1
                        }
                    } label: {
                        Label("Exit Recovery / Normal Reboot", systemImage: "arrow.counterclockwise.circle.fill")
                    }
                    .buttonStyle(.bordered)

                    Button {
                        Task {
                            actionStatus = "Dispatching revive..."
                            let res = await engine.reviveAppleDevice()
                            actionStatus = res.1
                        }
                    } label: {
                        Label("Revive (Retain Data)", systemImage: "heart.text.square.fill")
                    }
                    .buttonStyle(.bordered)
                }

                if !actionStatus.isEmpty {
                    Text(actionStatus)
                        .font(.system(size: 10.5, design: .monospaced))
                        .foregroundColor(.blue)
                        .padding(.top, 2)
                }
            }
            .padding(8)
        }
    }

    @ViewBuilder
    private var guidedCountdownCard: some View {
        GroupBox(label: Label("Guided Physical DFU Mode Countdown Wizard", systemImage: "timer")) {
            VStack(alignment: .leading, spacing: 12) {
                // Device Family Selector
                Picker("Device Family", selection: $selectedFamily) {
                    ForEach(DeviceFamily.allCases) { fam in
                        Text(fam.shortName).tag(fam)
                    }
                }
                .pickerStyle(.segmented)

                // Instruction Checklist
                VStack(alignment: .leading, spacing: 4) {
                    instructionsView
                }
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))

                // Active Stage Display
                stageInteractiveView

                // Action Controls Bar
                HStack(spacing: 12) {
                    if isCountingDown {
                        Button("Cancel Countdown") {
                            cancelCountdown()
                        }
                        .buttonStyle(.bordered)
                        .tint(.red)
                    } else {
                        Button {
                            startCountdown()
                        } label: {
                            Label("▶ Start Guided DFU Countdown", systemImage: "play.circle.fill")
                                .font(.system(size: 12, weight: .bold))
                                .padding(.horizontal, 6)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.indigo)

                        if let ipsw = stagedIpswUrl, currentMode == .dfu || currentMode == .recovery {
                            Button {
                                Task {
                                    await engine.restoreAppleDeviceWithIpsw(path: ipsw.path, keepData: false)
                                }
                            } label: {
                                Label("⚡ Flash Staged IPSW (\(String(ipsw.lastPathComponent.prefix(18)))...)", systemImage: "bolt.fill")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.green)
                        }
                    }

                    Spacer()

                    Text("Auto-Sniffer: ACTIVE (500ms)")
                        .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                        .foregroundColor(.secondary)
                }
            }
            .padding(8)
        }
    }

    @ViewBuilder
    private var instructionsView: some View {
        switch selectedFamily {
        case .modernFaceId:
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "1.circle.fill").foregroundColor(.blue)
                Text("Quickly press & release **Volume Up**, then quickly press & release **Volume Down**.")
                    .font(.system(size: 11))
            }
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "2.circle.fill").foregroundColor(.blue)
                Text("Press and hold the **Side (Power) button** until the screen goes completely black.")
                    .font(.system(size: 11))
            }
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "3.circle.fill").foregroundColor(.blue)
                Text("Immediately hold **Side + Volume Down** for 5s, then release Side while keeping Volume Down held for 10s.")
                    .font(.system(size: 11))
            }
        case .iphone7:
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "1.circle.fill").foregroundColor(.blue)
                Text("Connect cable. Press and hold both **Side (Power) + Volume Down** buttons for 8 seconds.")
                    .font(.system(size: 11))
            }
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "2.circle.fill").foregroundColor(.blue)
                Text("Release **Side (Power)**, but **KEEP HOLDING Volume Down** for 10 seconds.")
                    .font(.system(size: 11))
            }
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "3.circle.fill").foregroundColor(.blue)
                Text("Screen stays black; computer grabs Apple DFU USB endpoint (PID 0x1227).")
                    .font(.system(size: 11))
            }
        case .homeButton:
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "1.circle.fill").foregroundColor(.blue)
                Text("Connect cable. Press and hold both **Power (Top/Side) + Home button** for 8 seconds.")
                    .font(.system(size: 11))
            }
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "2.circle.fill").foregroundColor(.blue)
                Text("Release **Power**, but **KEEP HOLDING Home button** for 10 seconds.")
                    .font(.system(size: 11))
            }
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "3.circle.fill").foregroundColor(.blue)
                Text("Screen stays black; computer grabs Apple DFU USB endpoint (PID 0x1227).")
                    .font(.system(size: 11))
            }
        }
    }

    @ViewBuilder
    private var stageInteractiveView: some View {
        switch phase {
        case .ready:
            HStack {
                Image(systemName: "hand.tap.fill")
                    .font(.title3)
                    .foregroundColor(.secondary)
                Text("Ready to begin. Place your fingers comfortably on the device buttons, then click 'Start Guided DFU Countdown'.")
                    .font(.system(size: 11.5))
                    .foregroundColor(.secondary)
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 6).stroke(Color.secondary.opacity(0.2)))

        case .preparing(let sec):
            HStack(spacing: 12) {
                Text("\(sec)")
                    .font(.system(size: 32, weight: .heavy, design: .monospaced))
                    .foregroundColor(.orange)
                VStack(alignment: .leading, spacing: 2) {
                    Text("GET READY...")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.orange)
                    Text("Hands on buttons! Countdown begins in \(sec) seconds...")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.12)))

        case .holdingCombo(let sec):
            HStack(spacing: 12) {
                Text("\(sec)s")
                    .font(.system(size: 32, weight: .heavy, design: .monospaced))
                    .foregroundColor(.blue)
                VStack(alignment: .leading, spacing: 2) {
                    Text(selectedFamily == .homeButton ? "HOLD POWER + HOME BUTTON TOGETHER!" : "HOLD SIDE + VOLUME DOWN TOGETHER!")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.blue)
                    Text("Keep holding both buttons firmly! (\(sec)s remaining)")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color.blue.opacity(0.12)))

        case .holdingSecond(let sec):
            HStack(spacing: 12) {
                Text("\(sec)s")
                    .font(.system(size: 32, weight: .heavy, design: .monospaced))
                    .foregroundColor(.red)
                VStack(alignment: .leading, spacing: 2) {
                    Text("⚠️ RELEASE POWER BUTTON NOW!")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.red)
                    Text(selectedFamily == .homeButton ? "KEEP HOLDING HOME BUTTON! Do not let go! (\(sec)s left)" : "KEEP HOLDING VOLUME DOWN! Do not let go! (\(sec)s left)")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color.red.opacity(0.12)))

        case .captured(let mode):
            HStack(spacing: 12) {
                Image(systemName: "checkmark.seal.fill")
                    .font(.title)
                    .foregroundColor(.green)
                VStack(alignment: .leading, spacing: 2) {
                    Text("🎉 HARDWARE CAPTURED & BOUND: \(mode.rawValue)")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.green)
                    Text("The USB endpoint has successfully transitioned. BobFWTools Studio has locked the target interface.")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color.green.opacity(0.15)))

        case .timedOut:
            HStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.title3)
                    .foregroundColor(.orange)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Device Did Not Transition to DFU Mode")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(.orange)
                    Text("If the device booted into normal iOS or Recovery, ensure the cable is firmly connected and try again.")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.12)))
        }
    }

    private func badgeColor(for mode: ServicingEngine.AppleUsbMode) -> Color {
        switch mode {
        case .dfu: return .green
        case .recovery: return .orange
        case .restoreOS: return .purple
        case .normal: return .blue
        case .none: return .secondary
        }
    }

    private func autoSelectFamily() {
        let prod = engine.deviceProperties["ProductType"] ?? engine.lastObservedRecoveryProduct
        if prod.contains("iPhone9,") {
            selectedFamily = .iphone7
        } else if prod.contains("iPhone8,") || prod.contains("iPhone7,") || prod.contains("iPhone6,") || prod.contains("iPhone5,") {
            selectedFamily = .homeButton
        } else {
            selectedFamily = .modernFaceId
        }
    }

    private func startSniffer() {
        snifferTask?.cancel()
        snifferTask = Task {
            while !Task.isCancelled {
                await engine.refreshDevicesAndTelemetry()
                let mode = engine.detectedAppleMode
                if mode == .dfu || mode == .recovery {
                    await MainActor.run {
                        if case .captured = phase {
                            // already captured
                        } else if isCountingDown {
                            cancelCountdown()
                            NSSound.beep()
                            phase = .captured(mode: mode)
                        } else if mode == .dfu {
                            phase = .captured(mode: mode)
                        }
                    }
                }
                try? await Task.sleep(nanoseconds: 500_000_000)
            }
        }
    }

    private func startCountdown() {
        cancelCountdown()
        phase = .preparing(seconds: 3)

        countdownTask = Task {
            for s in stride(from: 3, through: 1, by: -1) {
                if Task.isCancelled { return }
                await MainActor.run { phase = .preparing(seconds: s) }
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }

            let holdDuration = comboSeconds
            for s in stride(from: holdDuration, through: 1, by: -1) {
                if Task.isCancelled { return }
                await MainActor.run { phase = .holdingCombo(seconds: s) }
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }

            NSSound.beep()
            for s in stride(from: 10, through: 1, by: -1) {
                if Task.isCancelled { return }
                await MainActor.run { phase = .holdingSecond(seconds: s) }
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }

            if !Task.isCancelled {
                await MainActor.run {
                    let mode = engine.detectedAppleMode
                    if mode == .dfu || mode == .recovery {
                        phase = .captured(mode: mode)
                    } else {
                        phase = .timedOut
                    }
                }
            }
        }
    }

    private func cancelCountdown() {
        countdownTask?.cancel()
        countdownTask = nil
    }

    private func cancelTimers() {
        countdownTask?.cancel()
        countdownTask = nil
        snifferTask?.cancel()
        snifferTask = nil
    }
}

// MARK: - Module 7: Audited Jobs, Repair Notes & Windows .EXE / UTM Bridge

struct BobFWTelemetryLedgerCard: View {
    @ObservedObject private var logger = BobFWTelemetryLogger.shared

    var body: some View {
        GroupBox(label: Label("Multi-Platform Hardware Telemetry Ledger (\(logger.historicalLedger.count) events)", systemImage: "waveform.path.badge.plus")) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Asynchronous thread-isolated telemetry records across chipset and transport pipelines:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    if !logger.historicalLedger.isEmpty {
                        Button("Clear Ledger") {
                            logger.historicalLedger.removeAll()
                        }
                        .controlSize(.small)
                    }
                }

                if logger.historicalLedger.isEmpty {
                    Text("No telemetry events recorded yet. Execute any diagnostic, guided wizard, or restoration workflow to populate.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 8)
                } else {
                    ScrollView {
                        VStack(spacing: 6) {
                            ForEach(logger.historicalLedger.reversed()) { record in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text("[\(record.workflowId)]")
                                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        if let chip = record.hardwareProfile?.chipset {
                                            Text(chip.rawValue)
                                                .font(.system(size: 9.5, design: .monospaced))
                                                .padding(.horizontal, 4)
                                                .padding(.vertical, 1)
                                                .background(RoundedRectangle(cornerRadius: 3).fill(Color.blue.opacity(0.15)))
                                                .foregroundColor(.blue)
                                        }
                                        Spacer()
                                        Text(record.executionStatus.rawValue)
                                            .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 5)
                                            .padding(.vertical, 2)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(statusBackground(record.executionStatus)))
                                            .foregroundColor(statusForeground(record.executionStatus))
                                    }

                                    if let exc = record.capturedException {
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text("Domain: \(exc.errorDomain) (Code \(exc.systemErrorCode))")
                                                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                                                .foregroundColor(.red)
                                            if !exc.lowerLevelRawOutput.isEmpty {
                                                Text(exc.lowerLevelRawOutput)
                                                    .font(.system(size: 9.5, design: .monospaced))
                                                    .foregroundColor(.secondary)
                                                    .lineLimit(2)
                                            }
                                            Text("Mitigation: \(exc.targetedMitigationAdvice)")
                                                .font(.system(size: 9.5, weight: .medium))
                                                .foregroundColor(.accentColor)
                                        }
                                        .padding(4)
                                        .background(RoundedRectangle(cornerRadius: 4).fill(Color.red.opacity(0.08)))
                                    }
                                }
                                .padding(6)
                                .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                            }
                        }
                    }
                    .frame(height: 160)
                }
            }
            .padding(8)
        }
    }

    private func statusBackground(_ status: BobFWTelemetryLogger.OperationalStatus) -> Color {
        switch status {
        case .success: return Color.green.opacity(0.2)
        case .executing, .processStaged: return Color.blue.opacity(0.2)
        case .faultInterrupted: return Color.red.opacity(0.2)
        case .busTimeout: return Color.orange.opacity(0.2)
        }
    }

    private func statusForeground(_ status: BobFWTelemetryLogger.OperationalStatus) -> Color {
        switch status {
        case .success: return .green
        case .executing, .processStaged: return .blue
        case .faultInterrupted: return .red
        case .busTimeout: return .orange
        }
    }
}

struct JobsNotesAndBridgeView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var exePath: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ModuleHeader(
                title: "Audited Workflow Jobs, Repair Receipts & UTM Bridge",
                subtitle: "Export BobFWTools JSON/Markdown diagnostic receipts, record per-session repair notes, and bridge to UTM/Wine"
            )

            // Repair Notes & Receipt Export
            GroupBox(label: Label("Technician Repair Notes & Diagnostic Receipt Exporter", systemImage: "doc.text.magnifyingglass")) {
                VStack(alignment: .leading, spacing: 10) {
                    TextEditor(text: $engine.repairNotes)
                        .font(.system(size: 12, design: .monospaced))
                        .frame(height: 90)
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.secondary.opacity(0.25)))

                    HStack(spacing: 10) {
                        Button("Save Repair Notes") {
                            engine.saveRepairNotes()
                        }
                        Button("Export Diagnostic JSON Receipt...") {
                            exportReceiptJSON()
                        }
                        Button("Generate Customer Intake Sheet (.pdf)...") {
                            exportIntakePDF()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding(8)
            }

            // Audited Job History
            GroupBox(label: Label("Audited Workflow Job Trail (\(engine.jobs.count) jobs)", systemImage: "clock.arrow.circlepath")) {
                VStack(alignment: .leading, spacing: 6) {
                    if engine.jobs.isEmpty {
                        Text("No workflow jobs recorded yet in this session.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(engine.jobs.prefix(10)) { job in
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("[\(job.workflowId)] \(job.title)")
                                        .font(.system(size: 12, weight: .semibold))
                                    Text(job.summary)
                                        .font(.system(size: 11, design: .monospaced))
                                        .foregroundColor(.secondary)
                                        .lineLimit(1)
                                }
                                Spacer()
                                Text(job.state.uppercased())
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundColor(job.verified ? .green : .orange)
                            }
                            .padding(6)
                            .background(RoundedRectangle(cornerRadius: 6).fill(Color(NSColor.controlBackgroundColor)))
                        }
                    }
                }
                .padding(8)
            }

            // Real-Time Asynchronous Telemetry Isolation Ledger
            BobFWTelemetryLedgerCard()

            // UTM & Wine Bridge
            GroupBox(label: Label("USB Passthrough VM Bridge", systemImage: "macwindow.on.rectangle")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        TextField("Optional: Path to external binary...", text: $exePath)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))

                        Button("Locate Binary...") {
                            if let path = pickFile(allowedExtensions: ["exe", "msi"]) {
                                exePath = path
                            }
                        }
                    }

                    HStack(spacing: 12) {
                        Button {
                            NSWorkspace.shared.open(URL(fileURLWithPath: "/Applications/UTM.app"))
                            engine.log(.info, "Launched /Applications/UTM.app for USB Passthrough environment.")
                        } label: {
                            Label("Launch UTM.app (Full USB Passthrough)", systemImage: "play.desktopcomputer")
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding(8)
            }
        }
    }

    private func exportReceiptJSON() {
        let savePanel = NSSavePanel()
        savePanel.nameFieldStringValue = "bobfwtools-diagnostic-receipt-\(Int(Date().timeIntervalSince1970)).json"
        guard savePanel.runModal() == .OK, let url = savePanel.url else { return }

        let payload: [String: Any] = [
            "application": "BobFWTools — Bobby's Workshop (Phoenix Forge)",
            "exportedAt": ISO8601DateFormatter().string(from: Date()),
            "connectionGrade": engine.connectionGrade,
            "samsungModemTarget": [
                "model": engine.samsungModemInfo?.model ?? "",
                "pdaVersion": engine.samsungModemInfo?.pdaVersion ?? "",
                "cscPackageVersion": engine.samsungModemInfo?.cscPackageVersion ?? "",
                "activeCsc": engine.samsungModemInfo?.activeCsc ?? "",
                "countryCode": engine.samsungModemInfo?.countryCode ?? "",
                "serialNumber": engine.samsungModemInfo?.serialNumber ?? "",
                "carrierLock": engine.samsungModemInfo?.carrierLock ?? ""
            ],
            "repairNotes": engine.repairNotes,
            "jobsCount": engine.jobs.count
        ]

        if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: url)
            engine.log(.success, "Exported BobFWTools Diagnostic Receipt to \(url.path)")
        }
    }

    private func exportIntakePDF() {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [.pdf]
        savePanel.nameFieldStringValue = "bobfwtools-customer-intake-\(Int(Date().timeIntervalSince1970)).pdf"
        guard savePanel.runModal() == .OK, let url = savePanel.url else { return }

        if let pdfData = engine.generateCustomerIntakePdf(
            ticketId: "TKT-\(Int.random(in: 10000...99999))",
            customerName: "Customer Bench Intake",
            technician: "Bobby Blanco"
        ) {
            do {
                try pdfData.write(to: url)
                engine.log(.success, "✔ Generated printable Customer Intake Sheet: \(url.path)")
                NSWorkspace.shared.open(url)
            } catch {
                engine.log(.error, "✖ Failed to write PDF report: \(error.localizedDescription)")
            }
        } else {
            engine.log(.error, "✖ Failed to generate Customer Intake PDF report.")
        }
    }
}

// MARK: - Right Console Panel & Telemetry Visualizer

enum ConsoleDisplayMode: String, CaseIterable {
    case engineLogs = "Execution Logs"
    case telemetry = "Telemetry Visualizer"
    case dualTiles = "Live Dual Monitor"
}

// MARK: - Automated Database Size Monitor Pane

struct BobFWDatabaseMonitorView: View {
    @ObservedObject private var logger = BobFWTelemetryLogger.shared
    @State private var loggedRowsCount: Int = 0
    @State private var databaseSizeString: String = "0 KB"

    private let monitoringTimer = Timer.publish(every: 2.0, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "square.stack.3d.up.fill")
                    .font(.title2)
                    .foregroundColor(.orange)

                VStack(alignment: .leading, spacing: 2) {
                    Text("SQLite Audit Ledger Storage Monitor")
                        .font(.headline)
                    Text("Target Workspace File Vector Tracking Allocation")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                Spacer()

                Button(action: { refreshStorageMetrics() }) {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.plain)
            }

            Divider()

            HStack(spacing: 20) {
                // Metric Node 1: Log Volume Count
                VStack(alignment: .leading, spacing: 4) {
                    Text("COMMITTED ENTRIES")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.gray)
                    Text("\(loggedRowsCount)")
                        .font(.system(size: 22, weight: .bold, design: .monospaced))
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                // Metric Node 2: Database Allocation Size
                VStack(alignment: .leading, spacing: 4) {
                    Text("LEDGER DISK SPACE")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.gray)
                    Text(databaseSizeString)
                        .font(.system(size: 22, weight: .bold, design: .monospaced))
                        .foregroundColor(.cyan)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(.vertical, 4)

            // Operational Safety Action Button
            Button(action: {
                logger.purgeTelemetryLedger()
                refreshStorageMetrics()
            }) {
                HStack {
                    Spacer()
                    Image(systemName: "bolt.fill")
                    Text("Purge Offline Ledger Indices")
                    Spacer()
                }
            }
            .buttonStyle(.bordered)
            .tint(.orange)
        }
        .padding()
        .background(Color(NSColor.windowBackgroundColor).opacity(0.8))
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.gray.opacity(0.2), lineWidth: 1))
        .onAppear { refreshStorageMetrics() }
        .onReceive(monitoringTimer) { _ in refreshStorageMetrics() }
    }

    /// Queries metrics directly from file indices and formats them for the user
    private func refreshStorageMetrics() {
        let stats = logger.fetchDatabaseStorageMetrics()
        self.loggedRowsCount = stats.rowCount

        let byteFormatter = ByteCountFormatter()
        byteFormatter.allowedUnits = [.useKB, .useMB]
        byteFormatter.countStyle = .file
        self.databaseSizeString = byteFormatter.string(fromByteCount: stats.sizeInBytes)
    }
}

struct BobFWTelemetryConsoleView: View {
    @ObservedObject private var telemetry = BobFWTelemetryLogger.shared
    @State private var filterQuery: String = ""
    @State private var autoScrollToBottom: Bool = true
    @State private var showDatabaseMonitor: Bool = false

    var filteredLogs: [BobFWTelemetryLogger.PipelineSessionRecord] {
        if filterQuery.isEmpty { return telemetry.historicalLedger }
        return telemetry.historicalLedger.filter { $0.workflowId.localizedCaseInsensitiveContains(filterQuery) }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Live Status Header Toolbar
            HStack {
                TextField("Filter by Workflow ID...", text: $filterQuery)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(size: 11, design: .monospaced))

                Button {
                    telemetry.historicalLedger.removeAll()
                } label: {
                    Label("Clear", systemImage: "trash")
                }
                .controlSize(.small)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // Collapsible SQLite Audit Ledger Storage Monitor
            DisclosureGroup(
                isExpanded: $showDatabaseMonitor,
                content: {
                    BobFWDatabaseMonitorView()
                        .padding(8)
                },
                label: {
                    HStack(spacing: 6) {
                        Image(systemName: "cylinder.split.1x2.fill")
                            .foregroundColor(.orange)
                        Text("Audit Ledger Storage Monitor")
                            .font(.system(size: 11, weight: .semibold))
                        Spacer()
                    }
                    .padding(.horizontal, 4)
                }
            )
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color(NSColor.controlBackgroundColor).opacity(0.5))

            Divider()

            // Scrolling Live Terminal Log Layout
            ScrollViewReader { proxy in
                List(filteredLogs) { record in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(record.timestamp, style: .time)
                                .font(.system(.caption, design: .monospaced))
                                .foregroundColor(.secondary)

                            Text("[\(record.workflowId)]")
                                .font(.system(.caption, design: .monospaced))
                                .foregroundColor(.orange)

                            Spacer()

                            // Badge indicating precise execution status state
                            Text(record.executionStatus.rawValue)
                                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(statusColorModifier(record.executionStatus).opacity(0.2))
                                .foregroundColor(statusColorModifier(record.executionStatus))
                                .cornerRadius(4)
                        }

                        if let profile = record.hardwareProfile {
                            Text("Target: \(profile.chipset.rawValue) · Transport: \(profile.activeTransport.rawValue)")
                                .font(.system(size: 10.5, design: .monospaced))
                                .foregroundColor(.accentColor)
                        }

                        // Render Exception Box only if process fault is trapped
                        if let fault = record.capturedException {
                            VStack(alignment: .leading, spacing: 3) {
                                Text("⚠️ FAULT [\(fault.errorDomain)] CODE: \(fault.systemErrorCode)")
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundColor(.red)

                                if !fault.lowerLevelRawOutput.isEmpty {
                                    Text("Raw: \(fault.lowerLevelRawOutput)")
                                        .font(.system(size: 9.5, design: .monospaced))
                                        .foregroundColor(.secondary)
                                        .lineLimit(2)
                                }

                                Text("Mitigation Advice: \(fault.targetedMitigationAdvice)")
                                    .font(.system(size: 10, weight: .medium))
                                    .foregroundColor(.green)
                            }
                            .padding(6)
                            .background(RoundedRectangle(cornerRadius: 4).fill(Color.red.opacity(0.12)))
                        }
                    }
                    .padding(.vertical, 2)
                    .id(record.id)
                }
                .onChange(of: telemetry.historicalLedger.count) { _ in
                    if autoScrollToBottom, let lastRecord = filteredLogs.last {
                        withAnimation { proxy.scrollTo(lastRecord.id, anchor: .bottom) }
                    }
                }
            }
        }
    }

    private func statusColorModifier(_ status: BobFWTelemetryLogger.OperationalStatus) -> Color {
        switch status {
        case .processStaged: return .gray
        case .executing: return .yellow
        case .success: return .green
        case .faultInterrupted, .busTimeout: return .red
        }
    }
}

struct ConsoleLogPanel: View {
    @ObservedObject var engine: ServicingEngine
    @Binding var customCommand: String
    @State private var consoleMode: ConsoleDisplayMode = .engineLogs

    private static let timeFormatter: DateFormatter = {
        let df = DateFormatter()
        df.dateFormat = "HH:mm:ss"
        return df
    }()

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Picker("", selection: $consoleMode) {
                    ForEach(ConsoleDisplayMode.allCases, id: \.self) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 330)

                Spacer()

                if consoleMode == .engineLogs {
                    Button("Copy") {
                        let allText = engine.logs.map { "[\(Self.timeFormatter.string(from: $0.timestamp))] [\($0.level.rawValue)] \($0.message)" }.joined(separator: "\n")
                        NSPasteboard.general.clearContents()
                        NSPasteboard.general.setString(allText, forType: .string)
                    }
                    .controlSize(.small)

                    Button("Clear") {
                        engine.clearLogs()
                    }
                    .controlSize(.small)
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            if consoleMode == .telemetry {
                BobFWTelemetryConsoleView()
            } else if consoleMode == .dualTiles {
                VStack(spacing: 8) {
                    BobFWDatabaseMonitorView()
                        .padding(.horizontal, 8)
                        .padding(.top, 8)
                    BobFWTelemetryConsoleView()
                }
            } else {
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 6) {
                            ForEach(engine.logs) { item in
                                HStack(alignment: .top, spacing: 8) {
                                    Text(Self.timeFormatter.string(from: item.timestamp))
                                        .font(.system(size: 11, design: .monospaced))
                                        .foregroundColor(.secondary)

                                    Text(item.level.rawValue)
                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 1)
                                        .background(RoundedRectangle(cornerRadius: 4).fill(badgeColor(item.level).opacity(0.2)))
                                        .foregroundColor(badgeColor(item.level))

                                    Text(item.message)
                                        .font(.system(size: 11.5, design: .monospaced))
                                        .foregroundColor(.primary)
                                        .textSelection(.enabled)
                                }
                                .id(item.id)
                            }
                        }
                        .padding(12)
                    }
                    .background(Color(NSColor.textBackgroundColor))
                    .onChange(of: engine.logs.count) { _ in
                        if let last = engine.logs.last {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }

                Divider()

                // Quick Shell / ADB / BootForge Command Bar
                HStack(spacing: 8) {
                    TextField("Run direct adb / fastboot / bootforgeusb command...", text: $customCommand)
                        .textFieldStyle(.roundedBorder)
                        .font(.system(size: 12, design: .monospaced))
                        .onSubmit {
                            runCustomShell()
                        }
                    Button("Run") {
                        runCustomShell()
                    }
                }
                .padding(10)
                .background(Color(NSColor.controlBackgroundColor))
            }
        }
    }

    private func runCustomShell() {
        let cmd = customCommand.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cmd.isEmpty else { return }
        customCommand = ""
        Task {
            _ = await engine.executeAndLog(
                workflowId: "console.custom",
                title: cmd,
                executable: "/bin/sh",
                arguments: ["-c", cmd]
            )
        }
    }

    private func badgeColor(_ level: LogEntry.Level) -> Color {
        switch level {
        case .info: return .blue
        case .command: return .purple
        case .success: return .green
        case .warning: return .orange
        case .error: return .red
        }
    }
}

// MARK: - Shared UI Helpers

struct ModuleHeader: View {
    let title: String
    let subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 19, weight: .bold))
            Text(subtitle)
                .font(.system(size: 12))
                .foregroundColor(.secondary)
        }
    }
}

@MainActor
func pickFile(allowedExtensions: [String]) -> String? {
    let panel = NSOpenPanel()
    panel.canChooseFiles = true
    panel.canChooseDirectories = false
    panel.allowsMultipleSelection = false
    if !allowedExtensions.isEmpty {
        panel.allowedContentTypes = allowedExtensions.compactMap { UTType(filenameExtension: $0) }
    }
    return panel.runModal() == .OK ? panel.url?.path : nil
}

@MainActor
func pickDirectory() -> String? {
    let panel = NSOpenPanel()
    panel.canChooseFiles = false
    panel.canChooseDirectories = true
    panel.allowsMultipleSelection = false
    return panel.runModal() == .OK ? panel.url?.path : nil
}

// MARK: - Developer Utility Workbench & Live Logcat View

struct DeveloperWorkbenchView: View {
    @ObservedObject var engine: ServicingEngine
    @State private var selectedApkPath: String = ""
    @State private var deploymentStatus: String = "Idle"
    @State private var searchPattern: String = ""
    @State private var selectedLocale: String = "en-US"

    let commonLocales = [
        ("en-US", "English (United States)"),
        ("es-US", "Spanish (Estados Unidos)"),
        ("fr-FR", "French (France)"),
        ("de-DE", "German (Deutschland)"),
        ("ar-SA", "Arabic (العربية)"),
        ("zh-CN", "Chinese Simplified (简体中文)"),
        ("ja-JP", "Japanese (日本語)"),
        ("ko-KR", "Korean (한국어)"),
        ("pt-BR", "Portuguese (Brasil)"),
        ("ru-RU", "Russian (Русский)")
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            ModuleHeader(
                title: "Developer Workbench & Live Staging Suite",
                subtitle: "Automated JSON debloat management, bulk APK sideload siphon, live regex-filtered logcat streaming, and locale stager"
            )

            // Multi-Brand Hardware Diagnostic Codes & Secret Menu Hub
            MultiBrandHardwareDiagnosticHubCard(engine: engine)

            // Wireless ADB Pairing & Connection Bridge
            WirelessAdbBridgeCard(engine: engine)

            // Section 1: 1-Click System Locale Staging Engine
            GroupBox(label: Label("System Localization & Locale Stager (Authorized ADB)", systemImage: "globe")) {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Stage device language and system locales without wiping or navigating Settings menus:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 12) {
                        Picker("Select Locale:", selection: $selectedLocale) {
                            ForEach(commonLocales, id: \.0) { loc in
                                Text("\(loc.1) [\(loc.0)]").tag(loc.0)
                            }
                        }
                        .frame(width: 320)

                        Button("Apply System Locale") {
                            Task {
                                let (ok, msg) = await engine.setDeviceLocale(selectedLocale)
                                if ok {
                                    engine.log(.success, "✔ Applied locale: \(selectedLocale)")
                                } else {
                                    engine.log(.error, "✖ Failed to apply locale: \(msg)")
                                }
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!engine.devices.contains { $0.transport == .adb })
                    }
                }
                .padding(8)
            }

            // Section 2: Automated JSON Debloat Registry Manager
            if let debloat = engine.debloatEngine {
                GroupBox(label: Label("Automated JSON Debloat Registry Manager (Reversible)", systemImage: "trash.circle.fill")) {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            Text("Strip carrier and OEM background bloatware for User 0 with 1-click restore:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Spacer()
                            Text(debloat.statusMessage)
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.secondary)
                        }

                        if debloat.progress > 0 && debloat.progress < 1.0 {
                            ProgressView(value: debloat.progress)
                                .padding(.vertical, 2)
                        }

                        // Category filtered package list
                        ScrollView {
                            VStack(spacing: 4) {
                                ForEach(debloat.registry) { pkg in
                                    HStack(spacing: 8) {
                                        Toggle(isOn: Binding(
                                            get: { debloat.selectedIds.contains(pkg.packageId) },
                                            set: { isSel in
                                                if isSel { debloat.selectedIds.insert(pkg.packageId) }
                                                else { debloat.selectedIds.remove(pkg.packageId) }
                                            }
                                        )) {
                                            HStack(spacing: 6) {
                                                Text(pkg.readableLabel)
                                                    .font(.system(size: 12, weight: .semibold))
                                                Text("(\(pkg.packageId))")
                                                    .font(.system(size: 10.5, design: .monospaced))
                                                    .foregroundColor(.secondary)
                                            }
                                        }

                                        Spacer()

                                        Text(pkg.category.rawValue)
                                            .font(.system(size: 9.5, design: .monospaced))
                                            .padding(.horizontal, 5)
                                            .padding(.vertical, 1)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(Color.blue.opacity(0.12)))
                                            .foregroundColor(.blue)

                                        Text(pkg.performanceImpact)
                                            .font(.system(size: 9.5, design: .monospaced))
                                            .padding(.horizontal, 5)
                                            .padding(.vertical, 1)
                                            .background(RoundedRectangle(cornerRadius: 3).fill(Color.orange.opacity(0.12)))
                                            .foregroundColor(.orange)

                                        if pkg.isInstalled {
                                            Text("INSTALLED")
                                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                                .foregroundColor(.green)
                                        } else {
                                            Button("Restore") {
                                                Task { await debloat.restorePackage(pkg.packageId) }
                                            }
                                            .controlSize(.mini)
                                        }
                                    }
                                    .padding(.vertical, 3)
                                    .padding(.horizontal, 6)
                                    .background(RoundedRectangle(cornerRadius: 4).fill(Color(NSColor.controlBackgroundColor)))
                                }
                            }
                        }
                        .frame(height: 180)

                        HStack(spacing: 10) {
                            Button("Scan Installed Bloat") {
                                Task { await debloat.scanInstalledState() }
                            }
                            .disabled(!engine.devices.contains { $0.transport == .adb })

                            Button {
                                Task { await debloat.uninstallSelected() }
                            } label: {
                                Label("Run 1-Click Debloat (Strip Selected)", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(!engine.devices.contains { $0.transport == .adb } || debloat.selectedIds.isEmpty)

                            Spacer()

                            Button("Select All") {
                                debloat.selectedIds = Set(debloat.registry.map { $0.packageId })
                            }
                            .controlSize(.small)

                            Button("Deselect All") {
                                debloat.selectedIds.removeAll()
                            }
                            .controlSize(.small)
                        }
                    }
                    .padding(8)
                }
            }

            // Section 3: 1-Click Bulk App Sideload Siphon (Watched Folder)
            if let siphon = engine.siphonEngine {
                GroupBox(label: Label("1-Click Bulk App Sideload Siphon (Watched Directory)", systemImage: "tray.and.arrow.down.fill")) {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(spacing: 10) {
                            Text("Watched Folder:")
                                .font(.caption.weight(.semibold))
                            Text(siphon.watchedDirectory?.path ?? "None")
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.secondary)
                                .lineLimit(1)

                            Spacer()

                            Button("Choose Folder...") {
                                if let chosen = pickDirectory() {
                                    siphon.setWatchedDirectory(URL(fileURLWithPath: chosen))
                                }
                            }

                            if let dir = siphon.watchedDirectory {
                                Button("Open in Finder") {
                                    NSWorkspace.shared.open(dir)
                                }
                            }
                        }

                        if siphon.isProcessing {
                            ProgressView(value: siphon.currentProgress)
                        }

                        // Queued APKs
                        ScrollView {
                            VStack(spacing: 4) {
                                if siphon.deploymentQueue.isEmpty {
                                    Text("No .apk installers found. Drop APK files into this folder to auto-populate the siphon queue.")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                        .padding(.vertical, 20)
                                } else {
                                    ForEach(siphon.deploymentQueue) { job in
                                        HStack {
                                            Image(systemName: "shippingbox.fill")
                                                .foregroundColor(.blue)
                                            Text(job.fileName)
                                                .font(.system(size: 11.5, design: .monospaced))
                                            Spacer()
                                            if let err = job.errorMessage {
                                                Text(err)
                                                    .font(.system(size: 10))
                                                    .foregroundColor(.red)
                                                    .lineLimit(1)
                                            }
                                            Text(job.status.uppercased())
                                                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                                .foregroundColor(statusColor(job.status))
                                        }
                                        .padding(.vertical, 3)
                                        .padding(.horizontal, 6)
                                        .background(RoundedRectangle(cornerRadius: 4).fill(Color(NSColor.controlBackgroundColor)))
                                    }
                                }
                            }
                        }
                        .frame(height: 140)

                        HStack(spacing: 12) {
                            Button {
                                Task { await siphon.executeBulkSideload() }
                            } label: {
                                Label("Deploy Siphon Queue (\(siphon.deploymentQueue.count) APKs)", systemImage: "arrow.down.circle.fill")
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(siphon.deploymentQueue.isEmpty || siphon.isProcessing || !engine.devices.contains { $0.transport == .adb })

                            Button("Rescan Folder") {
                                siphon.scanDirectory()
                            }

                            Spacer()

                            Text(siphon.statusSummary)
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(8)
                }
            }

            // Section 4: Single Diagnostic APK Sideloading (ABI Verified)
            GroupBox(label: Label("Single APK Deployment Bench (ABI Verified)", systemImage: "arrow.down.doc.fill")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        TextField("Path to .apk file...", text: $selectedApkPath)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 12, design: .monospaced))

                        Button("Choose APK...") {
                            if let path = pickFile(allowedExtensions: ["apk"]) {
                                selectedApkPath = path
                            }
                        }

                        Button {
                            deploySelectedApk()
                        } label: {
                            Label("Deploy APK", systemImage: "bolt.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(selectedApkPath.isEmpty || engine.isBusy)
                    }

                    HStack {
                        Text("Status: \(deploymentStatus)")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                }
                .padding(8)
            }

            // Section 5: Live Regex-Filtered Logcat Stream Subsystem
            GroupBox(label: Label("Live Device Logcat Stream Subsystem (adb logcat -v time)", systemImage: "waveform.path.ecg")) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        if engine.logcatSubsystem.isStreaming {
                            Button("Stop Logcat Stream") {
                                engine.logcatSubsystem.stop()
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.red)
                        } else {
                            Button("Start Live Logcat Stream") {
                                startLogcat()
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(!engine.devices.contains { $0.transport == .adb })
                        }

                        Button("Clear") {
                            engine.logcatSubsystem.clear()
                        }

                        Button("Export Logcat Report...") {
                            let target = engine.samsungModemInfo?.model ?? engine.selectedDevice?.name ?? "Unknown Target"
                            if let exportedUrl = engine.logcatSubsystem.exportReport(targetInfo: target) {
                                engine.log(.success, "Exported logcat report to \(exportedUrl.path)")
                            }
                        }
                        .disabled(engine.logcatSubsystem.filteredEntries.isEmpty)

                        Spacer()

                        Text("\(engine.logcatSubsystem.filteredEntries.count) events captured")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Image(systemName: "line.3.horizontal.decrease.circle")
                            .foregroundColor(.secondary)
                        TextField("Live regex filter (e.g. fatal|crash|anr|exception|activity)...", text: $searchPattern)
                            .textFieldStyle(.roundedBorder)
                            .font(.system(size: 11.5, design: .monospaced))
                            .onChange(of: searchPattern) { newVal in
                                engine.logcatSubsystem.applyFilter(newVal)
                            }
                    }

                    // Logcat Stream Viewport
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(alignment: .leading, spacing: 3) {
                                ForEach(engine.logcatSubsystem.filteredEntries) { entry in
                                    HStack(alignment: .top, spacing: 6) {
                                        Text(entry.timestamp)
                                            .font(.system(size: 10, design: .monospaced))
                                            .foregroundColor(.secondary)
                                        Text("[\(entry.logLevel)]")
                                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                                            .foregroundColor(colorForLevel(entry.logLevel))
                                        Text("\(entry.tag):")
                                            .font(.system(size: 10, weight: .semibold, design: .monospaced))
                                            .foregroundColor(.blue)
                                        Text(entry.message)
                                            .font(.system(size: 10.5, design: .monospaced))
                                            .foregroundColor(.primary)
                                            .textSelection(.enabled)
                                    }
                                    .id(entry.id)
                                }
                            }
                            .padding(8)
                        }
                        .frame(height: 220)
                        .background(Color(NSColor.textBackgroundColor))
                        .cornerRadius(6)
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.gray.opacity(0.2), lineWidth: 1))
                        .onChange(of: engine.logcatSubsystem.filteredEntries.count) { _ in
                            if let last = engine.logcatSubsystem.filteredEntries.last {
                                proxy.scrollTo(last.id, anchor: .bottom)
                            }
                        }
                    }
                }
                .padding(8)
            }
        }
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "Deployed": return .green
        case "Installing": return .blue
        case "Failed": return .red
        default: return .secondary
        }
    }

    private func colorForLevel(_ level: String) -> Color {
        switch level {
        case "E", "F": return .red
        case "W": return .orange
        case "D": return .green
        default: return .secondary
        }
    }

    private func deploySelectedApk() {
        guard !selectedApkPath.isEmpty else { return }
        deploymentStatus = "Verifying target CPU ABI..."
        Task {
            do {
                let url = URL(fileURLWithPath: selectedApkPath)
                let msg = try await engine.deployApk(url: url)
                deploymentStatus = "✔ \(msg)"
            } catch {
                deploymentStatus = "✖ \(error.localizedDescription)"
                engine.log(.error, "APK Deployment Error: \(error.localizedDescription)")
            }
        }
    }

    private func startLogcat() {
        let adbPath = engine.toolPaths["adb"] ?? "/usr/local/bin/adb"
        let args = engine.adbArgs(["logcat", "-v", "time"])
        engine.logcatSubsystem.start(adbPath: adbPath, args: args)
        engine.log(.info, "Started live logcat streaming from target device.")
    }
}


// MARK: - Pillar 9: High-Density Sidebar Metrics Viewport (ChipsetMetricsSidebarCard)

public struct ChipsetMetricsSidebarCard: View {
    public let definition: ChipsetSignatureDefinition?
    public let liveTemperature: Double

    public init(definition: ChipsetSignatureDefinition?, liveTemperature: Double) {
        self.definition = definition
        self.liveTemperature = liveTemperature
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "cpu")
                    .font(.title2)
                    .foregroundColor(.blue)
                VStack(alignment: .leading, spacing: 2) {
                    Text("SILICON INTERFACE ARCHITECTURE")
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundColor(.secondary)
                        .bold()
                    Text(definition?.marketingName ?? "Unresolved Processing Node")
                        .font(.headline)
                        .lineLimit(1)
                }
                Spacer()
                Text(definition?.architecture ?? "GENERIC")
                    .font(.system(.caption, design: .monospaced))
                    .bold()
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.12))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }

            Divider()

            if let chip = definition {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("Register Width").font(.caption).foregroundColor(.secondary)
                            Text("\(chip.bitness)-Bit Infrastructure").font(.subheadline).bold()
                        }
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text("Signature Pattern").font(.caption).foregroundColor(.secondary)
                            Text(chip.hvidSignaturePattern).font(.system(.caption2, design: .monospaced))
                        }
                    }

                    HStack {
                        VStack(alignment: .leading) {
                            Text("Core Thermal Layer").font(.caption).foregroundColor(.secondary)
                            if liveTemperature > 0 {
                                Text(String(format: "%.2f°C", liveTemperature))
                                    .font(.subheadline).bold()
                                    .foregroundColor(liveTemperature >= chip.thermalLimitCelsius ? .red : .green)
                            } else {
                                Text("Sensor Standby")
                                    .font(.subheadline).bold()
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text("Silicon Limit").font(.caption).foregroundColor(.secondary)
                            Text(String(format: "%.1f°C", chip.thermalLimitCelsius)).font(.subheadline).bold()
                        }
                    }
                }
                .textSelection(.enabled)

                if liveTemperature >= chip.thermalLimitCelsius && liveTemperature > 0 {
                    HStack {
                        Image(systemName: "exclamationmark.shield.fill")
                        Text("THERMAL BOUNDARY EXCEEDED: Silicon Throttling Operational").font(.system(.caption2, design: .monospaced))
                    }
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.red.opacity(0.12))
                    .foregroundColor(.red)
                    .cornerRadius(6)
                }
            } else {
                Text("Connect a verified target interface to decode underlying microarchitecture schemas.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 12)
            }
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
    }
}

// MARK: - Universal Multi-Brand Device Control & Power Hub Card

struct UniversalDeviceControlHubCard: View {
    @ObservedObject var engine: ServicingEngine
    @State private var controlActionStatus: String = ""

    private var activeBrandName: String {
        if let brand = engine.activeAndroidBrandProfile {
            return brand.brand.rawValue
        } else if let apple = engine.activeAppleProfile {
            return "Apple (\(apple.marketingName))"
        } else if let match = engine.universalMatch {
            return match.targetName
        }
        return "Standby"
    }

    private var hasAdb: Bool {
        engine.devices.contains { $0.transport == .adb }
    }

    private var hasFastboot: Bool {
        engine.devices.contains { $0.transport == .fastboot }
    }

    private var hasModemPort: Bool {
        !engine.serialPorts.isEmpty || engine.samsungModemInfo != nil
    }

    private var hasEdl: Bool {
        engine.usbDevices.contains { $0.vendorId == 0x05c6 && $0.productId == 0x9008 }
    }

    private var hasAndroidControlTransport: Bool {
        hasAdb || hasFastboot || hasModemPort || hasEdl
    }

    private var transportBadgeText: String {
        if engine.activePlatform == .appleIos {
            return "APPLE: \(engine.detectedAppleMode.rawValue.uppercased())"
        }
        var active: [String] = []
        if hasAdb { active.append("ADB AUTHORIZED") }
        if hasFastboot { active.append("FASTBOOT") }
        if hasModemPort { active.append("MODEM AT") }
        if hasEdl { active.append("EDL 9008") }
        if active.isEmpty {
            return engine.matrixRows.isEmpty ? "NO DEVICE" : "USB MTP / CHARGING (ADB OFF)"
        }
        return active.joined(separator: " · ")
    }

    var body: some View {
        GroupBox(label: Label("Universal Multi-Brand Device Control Hub (\(activeBrandName))", systemImage: "slider.horizontal.3")) {
            VStack(alignment: .leading, spacing: 10) {
                if engine.activePlatform == .none && engine.matrixRows.isEmpty {
                    HStack(spacing: 8) {
                        Image(systemName: "cable.connector")
                            .foregroundColor(.secondary)
                        Text("Connect any Android (ADB / Fastboot / MTP / EDL / BROM) or Apple (Normal / Recovery / DFU) device to unlock live hardware controls.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                } else if engine.activePlatform == .appleIos {
                    HStack(spacing: 10) {
                        Text(transportBadgeText)
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(RoundedRectangle(cornerRadius: 4).fill(Color.blue.opacity(0.16)))
                            .foregroundColor(.blue)

                        Button("Enter Recovery") {
                            Task {
                                let res = await engine.universalRebootTarget(toMode: "recovery")
                                controlActionStatus = res.message
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || engine.detectedAppleMode == .recovery || engine.detectedAppleMode == .dfu)

                        Button("Exit Recovery / Normal Reboot") {
                            Task {
                                let res = await engine.universalRebootTarget(toMode: "normal")
                                controlActionStatus = res.message
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.small)
                        .disabled(engine.isBusy)

                        Button("Query Live Signed IPSWs") {
                            Task { await engine.queryAppleFirmwaresOnline() }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || engine.isQueryingAppleFirmwares)

                        Spacer()
                    }
                } else {
                    HStack(spacing: 8) {
                        Text("TRANSPORT:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)
                        Text(transportBadgeText)
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(RoundedRectangle(cornerRadius: 4).fill((hasAndroidControlTransport ? Color.green : Color.orange).opacity(0.16)))
                            .foregroundColor(hasAndroidControlTransport ? .green : .orange)
                        Spacer()
                    }

                    if !hasAndroidControlTransport, let brand = engine.activeAndroidBrandProfile {
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "info.circle.fill")
                                .foregroundColor(.orange)
                            VStack(alignment: .leading, spacing: 2) {
                                Text("USB Connected Only (ADB & Fastboot Inactive) — Enable Control Mode:")
                                    .font(.system(size: 10.5, weight: .bold))
                                    .foregroundColor(.orange)
                                Text("• USB Debugging: Settings → About Device → Tap Build Number 7× → Developer Options → USB Debugging ON.\n• Hardware Key Boot: \(brand.hardwareBootGuide)")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.10)))
                    }

                    HStack(spacing: 10) {
                        Text("1-CLICK REBOOT:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)

                        Button("Normal OS") {
                            Task {
                                let res = await engine.universalRebootTarget(toMode: "normal")
                                controlActionStatus = res.message
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || !hasAndroidControlTransport)

                        Button("Recovery") {
                            Task {
                                let res = await engine.universalRebootTarget(toMode: "recovery")
                                controlActionStatus = res.message
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || (!hasAdb && !hasFastboot && !hasModemPort))

                        Button("Bootloader / Fastboot") {
                            Task {
                                let res = await engine.universalRebootTarget(toMode: "bootloader")
                                controlActionStatus = res.message
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || (!hasAdb && !hasFastboot && !hasModemPort))

                        if engine.activeAndroidBrandProfile?.fastbootdSupported ?? true {
                            Button("Fastbootd (Userspace)") {
                                Task {
                                    let res = await engine.universalRebootTarget(toMode: "fastbootd")
                                    controlActionStatus = res.message
                                }
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                            .disabled(engine.isBusy || (!hasAdb && !hasFastboot))
                        }

                        if engine.activePlatform == .samsung {
                            Button("Download Mode") {
                                Task {
                                    let res = await engine.universalRebootTarget(toMode: "download")
                                    controlActionStatus = res.message
                                }
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                            .disabled(engine.isBusy || (!hasAdb && !hasModemPort))
                        }

                        Button("EDL 9008 Mode") {
                            Task {
                                let res = await engine.universalRebootTarget(toMode: "edl")
                                controlActionStatus = res.message
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || (!hasAdb && !hasFastboot))

                        Spacer()
                    }

                    HStack(spacing: 10) {
                        Text("BRAND ACTIONS:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)

                        Button {
                            Task {
                                let res = await engine.launchBrandDiagnosticTestMenu()
                                controlActionStatus = res.message
                            }
                        } label: {
                            Label("Dial Hardware Test Menu", systemImage: "phone.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.cyan)
                        .controlSize(.small)
                        .disabled(engine.isBusy || !hasAdb)

                        Button {
                            Task {
                                let res = await engine.fastbootSwitchActiveSlot()
                                controlActionStatus = res.message
                            }
                        } label: {
                            Label("Toggle A/B Slot", systemImage: "arrow.triangle.2.circlepath")
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || !hasFastboot)

                        Button {
                            Task {
                                let res = await engine.fastbootWipeUserData()
                                controlActionStatus = res.message
                            }
                        } label: {
                            Label("Fastboot Wipe (-w)", systemImage: "trash")
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(engine.isBusy || !hasFastboot)

                        Spacer()
                    }
                }

                if !controlActionStatus.isEmpty {
                    Text(controlActionStatus)
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.accentColor)
                }
            }
            .padding(8)
        }
    }
}

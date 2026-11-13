import SwiftUI

public struct BobFWTelemetryConsoleView: View {
    @ObservedObject private var telemetry = BobFWTelemetryLogger.shared
    @State private var filterQuery: String = ""
    @State private var autoScrollToBottom: Bool = true
    public init() {}

    var filteredLogs: [BobFWTelemetryLogger.PipelineSessionRecord] {
        if filterQuery.isEmpty { return telemetry.historicalLedger }
        return telemetry.historicalLedger.filter { $0.workflowId.localizedCaseInsensitiveContains(filterQuery) }
    }

    public var body: some View {
        VStack(spacing: 0) {
            HStack {
                Label("Studio Hardware Telemetry Log Engine", systemImage: "cpu.fill")
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
                TextField("Filter by Workflow ID...", text: $filterQuery)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 200)
                Button(action: { telemetry.historicalLedger.removeAll() }) {
                    Label("Purge View Engine Buffer", systemImage: "trash")
                }
                .buttonStyle(.bordered)
                .foregroundColor(.red)
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            ScrollViewReader { proxy in
                List(filteredLogs) { record in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(record.timestamp, style: .time)
                                .font(.system(.caption, design: .monospaced))
                                .foregroundColor(.gray)
                            Text("[\(record.workflowId)]")
                                .font(.system(.caption, design: .monospaced))
                                .foregroundColor(.orange)
                            Spacer()
                            Text(record.executionStatus.rawValue)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(statusColorModifier(record.executionStatus))
                                .foregroundColor(.black)
                                .cornerRadius(4)
                        }
                        if let profile = record.hardwareProfile {
                            Text("Target: \(profile.chipset.rawValue) | Transport Vector: \(profile.activeTransport.rawValue)")
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.cyan)
                        }
                        if let fault = record.capturedException {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("⚠️ FAULT [DOMAIN: \(fault.errorDomain)] - CODE: \(fault.systemErrorCode)")
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundColor(.red)
                                Text("Raw: \(fault.lowerLevelRawOutput)")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.gray)
                                Text("Bench Advice: \(fault.targetedMitigationAdvice)")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(.green)
                            }
                            .padding(8)
                            .background(Color.red.opacity(0.15))
                            .cornerRadius(4)
                        }
                    }
                    .padding(.vertical, 4)
                    .id(record.id)
                }
                .background(Color.black)
                .onChange(of: telemetry.historicalLedger.count) { _, _ in
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

public struct BobFWDatabaseMonitorView: View {
    @ObservedObject private var logger = BobFWTelemetryLogger.shared
    @State private var loggedRowsCount: Int = 0
    @State private var databaseSizeString: String = "0 KB"
    private let monitoringTimer = Timer.publish(every: 2.0, on: .main, in: .common).autoconnect()
    public init() {}

    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "square.stack.3d.up.fill")
                    .font(.title2)
                    .foregroundColor(.orange)
                VStack(alignment: .leading, spacing: 2) {
                    Text("SQLite Audit Ledger Storage Monitor").font(.headline)
                    Text("Target Workspace File Vector Tracking Allocation").font(.caption).foregroundColor(.gray)
                }
                Spacer()
                Button(action: { refreshStorageMetrics() }) { Image(systemName: "arrow.clockwise") }.buttonStyle(.plain)
            }
            Divider()
            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("COMMITTED ENTRIES").font(.system(size: 10, weight: .bold)).foregroundColor(.gray)
                    Text("\(loggedRowsCount)").font(.system(size: 22, weight: .bold, design: .monospaced))
                }
                VStack(alignment: .leading, spacing: 4) {
                    Text("LEDGER DISK SPACE").font(.system(size: 10, weight: .bold)).foregroundColor(.gray)
                    Text(databaseSizeString).font(.system(size: 22, weight: .bold, design: .monospaced)).foregroundColor(.cyan)
                }
            }
            Button(action: { logger.purgeTelemetryLedger(); refreshStorageMetrics() }) {
                HStack { Spacer(); Image(systemName: "bolt.fill"); Text("Purge Metrics Indices"); Spacer() }
            }
            .buttonStyle(.bordered).tint(.orange)
        }
        .padding()
        .background(Color(NSColor.windowBackgroundColor).opacity(0.8))
        .cornerRadius(8)
        .onAppear { refreshStorageMetrics() }
        .onReceive(monitoringTimer) { _ in refreshStorageMetrics() }
    }

    private func refreshStorageMetrics() {
        let stats = logger.fetchDatabaseStorageMetrics()
        self.loggedRowsCount = stats.rowCount
        let byteFormatter = ByteCountFormatter()
        byteFormatter.allowedUnits = [.useKB, .useMB]
        byteFormatter.countStyle = .file
        self.databaseSizeString = byteFormatter.string(fromByteCount: stats.sizeInBytes)
    }
}

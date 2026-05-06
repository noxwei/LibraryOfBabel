import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @StateObject private var viewModel = PipelineViewModel()

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Babel Importer")
                    .font(.system(size: 20, weight: .semibold, design: .monospaced))
                Spacer()
                if viewModel.isProcessing {
                    ProgressView()
                        .controlSize(.small)
                        .padding(.trailing, 4)
                    Text("Processing...")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
            .background(.bar)

            Divider()

            if viewModel.jobs.isEmpty {
                dropZone
            } else {
                ScrollView {
                    VStack(spacing: 12) {
                        dropZone
                            .frame(height: 120)

                        ForEach(viewModel.jobs) { job in
                            JobCardView(job: job)
                        }
                    }
                    .padding()
                }
            }
        }
        .frame(minWidth: 600, minHeight: 400)
    }

    private var dropZone: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(style: StrokeStyle(lineWidth: 2, dash: [8]))
                .foregroundStyle(viewModel.isDropTargeted ? .blue : .secondary.opacity(0.4))
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(viewModel.isDropTargeted ? Color.blue.opacity(0.05) : Color.clear)
                )

            VStack(spacing: 8) {
                Image(systemName: "book.closed")
                    .font(.system(size: 36))
                    .foregroundStyle(.secondary)
                Text("Drop EPUB files here")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                Text("or click to browse")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
        .frame(maxWidth: .infinity, minHeight: 160)
        .padding(viewModel.jobs.isEmpty ? 24 : 0)
        .onDrop(of: [.fileURL], isTargeted: $viewModel.isDropTargeted) { providers in
            viewModel.handleDrop(providers: providers)
            return true
        }
        .onTapGesture {
            viewModel.openFilePicker()
        }
    }
}

struct JobCardView: View {
    let job: ImportJob

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Job header
            HStack {
                Text(job.title)
                    .font(.system(.body, design: .monospaced, weight: .medium))
                    .lineLimit(1)
                Spacer()
                StatusBadge(status: job.overallStatus)
            }

            if let author = job.author {
                Text(author)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            // Pipeline stages
            HStack(spacing: 4) {
                ForEach(ImportStage.allCases, id: \.self) { stage in
                    StageIndicator(
                        stage: stage,
                        status: job.stageStatus(for: stage)
                    )
                    if stage != ImportStage.allCases.last {
                        Image(systemName: "chevron.right")
                            .font(.system(size: 8))
                            .foregroundStyle(.quaternary)
                    }
                }
            }

            // Details row
            if let detail = job.detail {
                Text(detail)
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(.background)
                .shadow(color: .black.opacity(0.06), radius: 2, y: 1)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(.separator.opacity(0.5))
        )
    }
}

struct StageIndicator: View {
    let stage: ImportStage
    let status: StageStatus

    var body: some View {
        HStack(spacing: 4) {
            statusIcon
                .font(.system(size: 10))
            Text(stage.label)
                .font(.system(.caption2, design: .monospaced))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: 4)
                .fill(backgroundColor)
        )
    }

    @ViewBuilder
    private var statusIcon: some View {
        switch status {
        case .pending:
            Image(systemName: "circle")
                .foregroundStyle(.quaternary)
        case .active:
            ProgressView()
                .controlSize(.mini)
        case .complete:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
        case .failed:
            Image(systemName: "xmark.circle.fill")
                .foregroundStyle(.red)
        }
    }

    private var backgroundColor: Color {
        switch status {
        case .pending: .clear
        case .active: .blue.opacity(0.08)
        case .complete: .green.opacity(0.06)
        case .failed: .red.opacity(0.06)
        }
    }
}

struct StatusBadge: View {
    let status: String

    var body: some View {
        Text(status.uppercased())
            .font(.system(.caption2, design: .monospaced, weight: .bold))
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(
                RoundedRectangle(cornerRadius: 3)
                    .fill(badgeColor.opacity(0.12))
            )
            .foregroundStyle(badgeColor)
    }

    private var badgeColor: Color {
        switch status {
        case "complete": .green
        case "failed": .red
        case "processing": .blue
        default: .secondary
        }
    }
}

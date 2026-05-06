import SwiftUI
import UniformTypeIdentifiers

enum ImportStage: String, CaseIterable {
    case imported = "imported"
    case chunking = "chunking"
    case embedding = "embedding"
    case complete = "complete"

    var label: String {
        switch self {
        case .imported: "Import"
        case .chunking: "Chunk"
        case .embedding: "Embed"
        case .complete: "Done"
        }
    }
}

enum StageStatus {
    case pending, active, complete, failed
}

struct ImportJob: Identifiable {
    let id: String
    let filename: String
    var title: String
    var author: String?
    var overallStatus: String
    var stages: [ImportStage: StageStatus]
    var detail: String?

    func stageStatus(for stage: ImportStage) -> StageStatus {
        stages[stage] ?? .pending
    }
}

@MainActor
class PipelineViewModel: ObservableObject {
    @Published var jobs: [ImportJob] = []
    @Published var isDropTargeted = false
    @Published var isProcessing = false

    private let api = PipelineAPI()
    private var pollingTasks: [String: Task<Void, Never>] = [:]

    func handleDrop(providers: [NSItemProvider]) {
        for provider in providers {
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
                guard let data = item as? Data,
                      let url = URL(dataRepresentation: data, relativeTo: nil),
                      url.pathExtension.lowercased() == "epub" else { return }
                Task { @MainActor in
                    await self.uploadFiles([url])
                }
            }
        }
    }

    func openFilePicker() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [UTType(filenameExtension: "epub")!]
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.message = "Select EPUB files to import into the Library of Babel"

        if panel.runModal() == .OK {
            Task {
                await uploadFiles(panel.urls)
            }
        }
    }

    func uploadFiles(_ urls: [URL]) async {
        isProcessing = true

        // Add placeholder jobs immediately
        for url in urls {
            let placeholderID = UUID().uuidString
            let job = ImportJob(
                id: placeholderID,
                filename: url.lastPathComponent,
                title: url.deletingPathExtension().lastPathComponent,
                overallStatus: "uploading",
                stages: [.imported: .active]
            )
            jobs.insert(job, at: 0)
        }

        do {
            let response = try await api.upload(fileURLs: urls)
            guard let data = response.data else {
                updatePlaceholders(urls: urls, status: "failed", detail: response.error)
                isProcessing = false
                return
            }

            // Replace placeholders with real job
            let jobID = data.job_id
            for (i, url) in urls.enumerated() {
                if let idx = jobs.firstIndex(where: { $0.filename == url.lastPathComponent && $0.overallStatus == "uploading" }) {
                    jobs[idx] = ImportJob(
                        id: "\(jobID)_\(i)",
                        filename: url.lastPathComponent,
                        title: url.deletingPathExtension().lastPathComponent,
                        overallStatus: "processing",
                        stages: [.imported: .complete, .chunking: .active]
                    )
                }
            }

            // Start polling
            startPolling(jobID: jobID)

        } catch {
            updatePlaceholders(urls: urls, status: "failed", detail: error.localizedDescription)
            isProcessing = false
        }
    }

    private func updatePlaceholders(urls: [URL], status: String, detail: String?) {
        for url in urls {
            if let idx = jobs.firstIndex(where: { $0.filename == url.lastPathComponent && $0.overallStatus == "uploading" }) {
                jobs[idx].overallStatus = status
                jobs[idx].stages[.imported] = .failed
                jobs[idx].detail = detail
            }
        }
    }

    private func startPolling(jobID: String) {
        pollingTasks[jobID]?.cancel()
        pollingTasks[jobID] = Task {
            while !Task.isCancelled {
                do {
                    try await Task.sleep(for: .seconds(1))
                    guard let status = try await api.status(jobID: jobID) else { continue }
                    updateFromStatus(status)

                    if status.status == "complete" || status.status == "failed" || status.status == "partial" {
                        isProcessing = jobs.contains { $0.overallStatus == "processing" || $0.overallStatus == "uploading" }
                        pollingTasks[jobID]?.cancel()
                        pollingTasks.removeValue(forKey: jobID)
                        break
                    }
                } catch {
                    if !Task.isCancelled {
                        try? await Task.sleep(for: .seconds(3))
                    }
                }
            }
        }
    }

    private func updateFromStatus(_ status: JobStatus) {
        guard let results = status.results, let progress = status.progress else {
            // No results yet — update current stage from progress
            if let currentStage = status.progress?.current_stage, let currentFile = status.progress?.current_file {
                if let idx = jobs.firstIndex(where: { $0.filename == currentFile || $0.title.contains(currentFile.replacingOccurrences(of: ".epub", with: "")) }) {
                    jobs[idx].overallStatus = "processing"
                    jobs[idx].stages = buildStages(from: currentStage)
                }
            }
            return
        }

        for result in results {
            let filename = result.filename
            guard let idx = jobs.firstIndex(where: { $0.filename == filename || $0.filename.contains(filename) }) else { continue }

            // Update title/author from extraction stage
            if let extraction = result.stages?["extraction"] {
                if let title = extraction.title { jobs[idx].title = title }
                if let author = extraction.author { jobs[idx].author = author }
            }

            // Update overall status
            jobs[idx].overallStatus = result.status

            // Update stages from result
            var stages: [ImportStage: StageStatus] = [:]

            if let ext = result.stages?["extraction"] {
                stages[.imported] = ext.status == "complete" ? .complete : .failed
            }
            if let chunk = result.stages?["chunking"] {
                stages[.chunking] = chunk.status == "complete" ? .complete : .failed
            }
            if let embed = result.stages?["embedding"] {
                switch embed.status {
                case "complete": stages[.embedding] = .complete
                case "in_progress": stages[.embedding] = .active
                case "failed": stages[.embedding] = .failed
                default: stages[.embedding] = .pending
                }
            }

            if result.status == "complete" {
                stages[.complete] = .complete
                if let bookID = result.book_id {
                    let chunks = result.stages?["chunking"]?.chunks_created ?? 0
                    let embedded = result.stages?["embedding"]?.chunks_embedded ?? 0
                    jobs[idx].detail = "book_id=\(bookID) | \(chunks) chunks | \(embedded) embedded"
                }
            } else if result.status == "failed" {
                stages[.complete] = .failed
                jobs[idx].detail = result.error
            }

            jobs[idx].stages = stages
        }

        // Handle files still in progress
        if let currentFile = progress.current_file, let currentStage = progress.current_stage {
            if let idx = jobs.firstIndex(where: { $0.overallStatus == "processing" && results.first(where: { $0.filename == $0.filename })?.status != "complete" }) {
                jobs[idx].stages = buildStages(from: currentStage)
            }
        }
    }

    private func buildStages(from currentStage: String) -> [ImportStage: StageStatus] {
        var stages: [ImportStage: StageStatus] = [:]
        let order: [String: ImportStage] = [
            "extracting": .imported,
            "chunking": .chunking,
            "embedding": .embedding,
            "ingesting": .chunking  // ingesting is part of the chunking phase visually
        ]

        guard let activeStage = order[currentStage] else {
            return [.imported: .active]
        }

        for stage in ImportStage.allCases {
            if stage.rawValue < activeStage.rawValue {
                stages[stage] = .complete
            } else if stage == activeStage {
                stages[stage] = .active
            } else {
                stages[stage] = .pending
            }
        }
        // Always mark imported as at least complete if we're past it
        if activeStage != .imported {
            stages[.imported] = .complete
        }
        return stages
    }
}

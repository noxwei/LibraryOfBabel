import Foundation

struct UploadResponse: Codable {
    let success: Bool
    let data: UploadData?
    let error: String?

    struct UploadData: Codable {
        let job_id: String
        let files_uploaded: Int
        let status: String
        let status_url: String?
        let files: [UploadedFile]?
    }

    struct UploadedFile: Codable {
        let filename: String
        let size_mb: Double?
        let status: String?
    }
}

struct StatusResponse: Codable {
    let success: Bool
    let data: JobStatus?
}

struct JobStatus: Codable {
    let job_id: String
    let status: String
    let created_at: String?
    let progress: JobProgress?
    let files: [FileEntry]?
    let results: [JobResult]?
    let errors: [String]?

    struct JobProgress: Codable {
        let total: Int?
        let processed: Int?
        let current_file: String?
        let current_stage: String?
    }

    struct FileEntry: Codable {
        let filename: String
        let size_mb: Double?
        let status: String?
    }

    struct JobResult: Codable {
        let filename: String
        let status: String
        let book_id: Int?
        let error: String?
        let stages: [String: StageInfo]?
    }

    struct StageInfo: Codable {
        let status: String?
        let title: String?
        let author: String?
        let chapters: Int?
        let words: Int?
        let chunks_created: Int?
        let book_id: Int?
        let chunks_ingested: Int?
        let chunks_embedded: Int?
        let chunks_total: Int?
        let model: String?
        let message: String?
        let error: String?
    }
}

actor PipelineAPI {
    let baseURL: String

    init(baseURL: String = "http://100.71.141.45:5564") {
        self.baseURL = baseURL
    }

    func upload(fileURLs: [URL]) async throws -> UploadResponse {
        let url = URL(string: "\(baseURL)/api/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 120

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        for fileURL in fileURLs {
            let fileData = try Data(contentsOf: fileURL)
            let filename = fileURL.lastPathComponent
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"files\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: application/epub+zip\r\n\r\n".data(using: .utf8)!)
            body.append(fileData)
            body.append("\r\n".data(using: .utf8)!)
        }
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(UploadResponse.self, from: data)
    }

    func status(jobID: String) async throws -> JobStatus? {
        let url = URL(string: "\(baseURL)/api/upload?job_id=\(jobID)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let response = try JSONDecoder().decode(StatusResponse.self, from: data)
        return response.data
    }
}

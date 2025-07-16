# MCP Endpoint Extension Plan

This document outlines a high‑level approach for extending the unified LibraryOfBabel API to integrate with an external **MCP (Master Control Program)**. The plan references the existing API design and configuration practices described in the documentation.

## 1. Review Current API

- The unified API exposes book listing, search, fuzzy search and health endpoints on **port 5562** as described in the [Endpoint Summary](ENDPOINT_SUMMARY.md).
- Authentication is required for all endpoints except `/health` using API keys, as documented in the [Unified API Reference](API-Reference-Unified.md).
- Configuration values such as `api_key` and `base_url` are managed centrally through `config/api_config.py` and `api_settings.json` (see [Centralized API Configuration Guide](CENTRALIZED_CONFIG_GUIDE.md)).

## 2. MCP Integration Objectives

1. **Expose MCP Service Endpoint** – provide a REST interface that the MCP can call for book and chunk data.
2. **Maintain Unified Security** – reuse existing API key authentication and rate limiting for MCP requests.
3. **Centralize Configuration** – add MCP credentials and endpoints to the centralized configuration system.
4. **Support Aggregation** – create endpoints that deliver summary data needed by MCP (e.g., total books, available embeddings).

## 3. Proposed Endpoint Additions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp/summary` | `GET` | Aggregate counts (books, chunks, embeddings, version info). |
| `/mcp/books` | `GET` | Paginated list of books for MCP synchronization. |
| `/mcp/chunks/{book_id}` | `GET` | Stream chunks for a given book. |

These endpoints will mirror the existing `/books` and `/chunks` functionality, but optimized for MCP synchronization (smaller default page sizes and optional delta parameters).

## 4. Security Considerations

- Reuse the authentication approaches outlined in the API reference:
  ```bash
  Authorization: Bearer YOUR_API_KEY
  ```
- Include rate limiting (60 requests per minute) for new MCP routes.
- Validate inputs using the same sanitation logic as existing endpoints.

## 5. Configuration Updates

- Extend `api_settings.json` to include MCP-specific fields:
  ```json
  "mcp": {
    "base_url": "https://mcp.example.com",
    "api_key": "mcp_key_here"
  }
  ```
- Update `config/api_config.py` so these values can be retrieved with `get_mcp_config()`.
- Document new options in the centralized configuration guide.

## 6. Implementation Steps

1. **Design Routes** – Add Flask routes under `src/api` with the `/mcp` prefix.
2. **Update Configuration** – Modify the centralized config to store MCP settings.
3. **Unit Tests** – Extend test suite to cover MCP endpoints (using the patterns in `tests/`).
4. **Documentation** – Update `API-Reference-Unified.md` and `ENDPOINT_SUMMARY.md` with new endpoints.
5. **Deployment** – Ensure port 5562 remains active and update any Launch Agent configuration if necessary.

## 7. Future Enhancements

- Provide webhook callbacks so MCP can receive updates automatically.
- Offer bulk export in a compressed format for initial MCP ingestion.
- Explore authentication with service tokens if MCP requires stricter security.

---

*This plan builds directly on the existing unified API and centralized configuration system, enabling a smooth extension to a Master Control Program while preserving the security and design principles already documented.*

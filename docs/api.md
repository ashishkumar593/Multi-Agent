# REST API Specification & Endpoint Reference

The AI Research & Report Agent exposes a REST API built with FastAPI, adhering strictly to OpenAPI 3.1 standards.

---

## 1. Base URL & Interactive Docs
- **Base URL**: `http://localhost:8000`
- **Interactive Swagger UI**: `/docs`
- **ReDoc Documentation**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`

---

## 2. Endpoints

### 2.1 Health Probes
- **`GET /health`**
  - **Description**: Returns runtime status and environment mode.
  - **Response 200 OK**:
    ```json
    {
      "status": "ok",
      "app": "AI Research & Report Agent",
      "env": "development"
    }
    ```

---

### 2.2 Autonomous Research Execution
- **`POST /api/v1/research`**
  - **Description**: Submits an open-ended research topic to the multi-agent system.
  - **Request Body**:
    ```json
    {
      "topic": "Impact of Generative AI on Software Engineering 2023-2026",
      "scope": "comprehensive",
      "max_iterations": 2
    }
    ```
  - **Response 200 OK**:
    ```json
    {
      "research_id": "job_a1b2c3d4e5f6",
      "topic": "Impact of Generative AI on Software Engineering 2023-2026",
      "status": "completed",
      "title": "Research Report: Impact of Generative AI on Software Engineering 2023-2026",
      "report_markdown": "# Research Report...",
      "comparison_table": "| Claim ID | Factual Assertion...",
      "references_markdown": "### References & Verified Sources...",
      "evidence_count": 8,
      "quality_score": 9.2
    }
    ```

---

### 2.3 Document Knowledge Base Ingestion
- **`POST /api/v1/documents`**
  - **Description**: Uploads a document (`.pdf`, `.docx`, `.txt`, `.md`), chunks it recursively, and indexes into Hybrid RAG.
  - **Request**: `multipart/form-data` with `file` binary.
  - **Response 200 OK**:
    ```json
    {
      "status": "success",
      "document": {
        "id": "doc_9f8e7d6c5b4a3210",
        "filename": "annual_tech_report.pdf",
        "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "chunks_count": 14,
        "size_bytes": 1048576
      }
    }
    ```

- **`GET /api/v1/documents`**
  - **Description**: Lists all indexed documents.
  - **Response 200 OK**:
    ```json
    [
      {
        "id": "doc_9f8e7d6c5b4a3210",
        "filename": "annual_tech_report.pdf",
        "chunks_count": 14,
        "size_bytes": 1048576
      }
    ]
    ```

---

### 2.4 Report Export
- **`GET /api/v1/reports/{report_id}/export`**
  - **Description**: Downloads generated report as a formatted PDF.
  - **Response 200 OK**: `application/pdf` binary stream.

# API Documentation

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication
No authentication is required. Chat responses need a valid `OPENAI_API_KEY` in `.env` to generate LLM answers; without it, the chat endpoint returns ranked search results only.

---

## Endpoints

### Health Check

#### GET /welcome
Returns application status and version information.

**Example:**
```bash
curl http://localhost:5000/api/v1/welcome
```

---

### Debug

#### GET /data/debug/files/{project_id}
List files that exist on disk for a project (helpful to confirm `file_id` values).

**Response:**
```json
{
  "project_id": "1",
  "project_path": "D:/Corsat/InteractiveBook/src/assets/files/1",
  "path_exists": true,
  "files": ["73peyf29g5ep_AIengineerupdated.pdf"],
  "file_count": 1
}
```

---

### Document Upload

#### POST /data/upload/{project_id}
Upload a document. Supported extensions: `pdf`, `txt`, `docx`, `md`, `csv`, `rtf`.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (file)

**File Requirements:**
- Max size: 10 MB
- Typical content types:
  - `application/pdf`
  - `text/plain`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
  - `text/markdown`
  - `text/csv`
  - `application/rtf`

**Response (200):**
```json
{
  "signal": "File uploaded successfully.",
  "file_id": "abc123_document.pdf",
  "project_id": "507f1f77bcf86cd799439011"
}
```

---

### Document Processing

#### POST /data/process/{project_id}
Load the file, chunk text, generate embeddings locally, save chunks to MongoDB, and store embeddings in ChromaDB.

**Request Body:**
```json
{
  "file_id": "abc123_document.pdf",
  "chunk_size": 1000,
  "overlap_size": 200,
  "do_reset": 0
}
```

**Response (200):**
```json
{
  "signal": "process success",
  "chunks_count": 150,
  "saved_count": 150,
  "embeddings_generated": 150,
  "chromadb_stored": true,
  "chromadb_count": 150
}
```

If the file is missing, the response includes the expected path and a sample of available files.

---

### Vector Search

#### POST /data/search/{project_id}
Semantic search over embeddings stored in ChromaDB.

**Request Body:**
```json
{
  "query": "Summarize the intro section",
  "top_k": 5,
  "file_id": null
}
```

**Response (200):**
```json
{
  "signal": "process success",
  "results": [
    {
      "chunk_text": "text...",
      "file_id": "abc123_document.pdf",
      "chunk_order": 12,
      "distance": 0.14,
      "metadata": { "page": 3 }
    }
  ],
  "count": 1,
  "query": "Summarize the intro section"
}
```

---

### RAG Chat

#### POST /data/chat/{project_id}
Retrieve context from ChromaDB and generate an answer with the configured LLM. If the LLM is unavailable, returns ranked search results instead.

**Request Body:**
```json
{
  "query": "What are the key takeaways?",
  "top_k": 5,
  "file_id": null
}
```

**Response with LLM (200):**
```json
{
  "signal": "process success",
  "answer": "The document highlights ...",
  "sources": [
    { "source_index": 1, "file_id": "abc123_document.pdf", "chunk_order": 4, "similarity": 0.82 }
  ],
  "query": "What are the key takeaways?",
  "chunks_retrieved": 5
}
```

**Response without LLM (200):**
```json
{
  "signal": "process success",
  "answer": null,
  "search_results": [
    { "source_index": 1, "file_id": "abc123_document.pdf", "chunk_order": 4, "similarity": 0.82 }
  ],
  "sources": [
    { "source_index": 1, "file_id": "abc123_document.pdf", "chunk_order": 4, "similarity": 0.82 }
  ],
  "query": "What are the key takeaways?",
  "chunks_retrieved": 5,
  "warning": "LLM generation failed, returning search results only"
}
```

---

## Response Signals

| Signal | Description |
|--------|-------------|
| `file_type_not_supported` | The uploaded file type is not supported |
| `file_size_exceeded` | The file size exceeds the maximum limit (10 MB) |
| `success_file_upload` | File uploaded successfully |
| `failed_file_upload` | File upload failed |
| `FILE_VALIDATED_SUCCESSFULLY` | File validation passed |
| `PROCESS_FAILED` | Document processing failed |
| `PROCESS_SUCCESS` | Document processing succeeded |

---

## Error Handling

Errors follow:

```json
{
  "signal": "Error message",
  "error": "Detailed error description (optional)"
}
```

HTTP status codes: `200`, `400`, `404`, `429`, `500`.

---

## File Processing Flow

1. **Upload** `/data/upload/{project_id}`  
   Save the file to `src/assets/files/{project_id}/{random}_{filename}` and return `file_id`.
2. **Process** `/data/process/{project_id}`  
   Load via LangChain loader (PDF/TXT/DOCX/MD/CSV/RTF), chunk text, generate embeddings, save to MongoDB + ChromaDB.
3. **Search** `/data/search/{project_id}`  
   Vector similarity search over stored embeddings.
4. **Chat** `/data/chat/{project_id}`  
   Retrieve context and generate an answer (LLM optional).

---

## Supported File Types

- PDF (`.pdf`)
- Text (`.txt`)
- Word (`.docx`)
- Markdown (`.md`)
- CSV (`.csv`)
- RTF (`.rtf`)

Images with OCR are planned.

---

## Best Practices

- Use the `file_id` returned from upload as-is when calling process/search/chat.
- Keep files under 10 MB.
- Default chunking works well for most docs (`chunk_size` 1000, `overlap_size` 200).
- If chat returns search results only, set `OPENAI_API_KEY` in `src/assets/.env`.

---

## Testing

You can test via Swagger UI (`/docs`), ReDoc (`/redoc`), `curl`, Postman, or your favorite HTTP client.

---

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue on GitHub
- Contact the maintainers


# API Documentation

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication
Currently, the API does not require authentication. Future versions will include JWT-based authentication.

---

## Endpoints

### Health Check

#### GET /welcome
Returns application status and version information.

**Response:**
```json
{
  "status": "running",
  "name": "InteractiveBook",
  "version": "1.0.0",
  "open_api_key": "sk-..."
}
```

**Example:**
```bash
curl http://localhost:5000/api/v1/welcome
```

---

### Document Upload

#### POST /data/upload/{project_id}
Upload a document (PDF or TXT).

**Path Parameters:**
- `project_id` (string, required): Project identifier (alphanumeric only)

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (file)

**File Requirements:**
- Allowed types: `application/pdf`, `text/plain`
- Maximum size: 10 MB (10485760 bytes)

**Response (Success - 200):**
```json
{
  "signal": "File uploaded successfully.",
  "file_id": "abc123_document.pdf",
  "project_id": "507f1f77bcf86cd799439011"
}
```

**Response (Error - 400):**
```json
{
  "signal": "File type not supported."
}
```

or

```json
{
  "signal": "File size exceeded the maximum limit."
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/v1/data/upload/project123" \
  -F "file=@document.pdf"
```

**Python Example:**
```python
import requests

with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/v1/data/upload/project123',
        files={'file': f}
    )
    print(response.json())
```

---

### Document Processing

#### POST /data/process/{project_id}
Process an uploaded document (chunking and embedding generation).

**Path Parameters:**
- `project_id` (string, required): Project identifier

**Request Body:**
```json
{
  "file_id": "abc123_document.pdf",
  "chunk_size": 100,
  "overlap_size": 20,
  "do_reset": 0
}
```

**Request Body Parameters:**
- `file_id` (string, required): The file ID returned from upload endpoint
- `chunk_size` (integer, optional): Size of text chunks (default: 100)
- `overlap_size` (integer, optional): Overlap between chunks (default: 20)
- `do_reset` (integer, optional): Reset processing (default: 0)

**Response (Success - 200):**
```json
{
  "signal": "process success",
  "chunks_count": 150
}
```

**Response (Error - 400):**
```json
{
  "signal": "process failed"
}
```

**Response (Error - 500):**
```json
{
  "signal": "process failed",
  "error": "Error message details"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/v1/data/process/project123" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "abc123_document.pdf",
    "chunk_size": 1000,
    "overlap_size": 200
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    'http://localhost:5000/api/v1/data/process/project123',
    json={
        'file_id': 'abc123_document.pdf',
        'chunk_size': 1000,
        'overlap_size': 200
    }
)
print(response.json())
```

---

## Response Signals

The API uses response signals to indicate the status of operations. All signals are defined in the `ResponseSignal` enum:

| Signal | Description |
|--------|-------------|
| `file_type_not_supported` | The uploaded file type is not supported |
| `file_size_exceeded` | The file size exceeds the maximum limit (10 MB) |
| `success_file_upload` | File uploaded successfully |
| `fialed_file_upload` | File upload failed |
| `FILE_VALIDATED_SUCCESSFULLY` | File validation passed |
| `PROCESS_FAILED` | Document processing failed |
| `PROCESS_SUCCESS` | Document processing succeeded |

---

## Error Handling

All errors follow a consistent format:

```json
{
  "signal": "Error message",
  "error": "Detailed error description (optional)"
}
```

### HTTP Status Codes

- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request (file type, size, missing parameters)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## File Processing Flow

1. **Upload**: Upload a file using `/data/upload/{project_id}`
   - File is validated (type and size)
   - File is saved to disk with a unique filename
   - Returns `file_id`

2. **Process**: Process the file using `/data/process/{project_id}`
   - File content is extracted (PDF or TXT)
   - Text is split into chunks
   - Chunks are ready for embedding generation (future)
   - Returns `chunks_count`

3. **Future: Embed & Store**: Generate embeddings and store in vector DB
4. **Future: Chat**: Query the document using natural language

---

## Supported File Types

### Currently Supported
- **PDF**: `.pdf` files (using PyMuPDF)
- **Text**: `.txt` files (UTF-8 encoding)

### Planned Support
- **Images**: JPG, PNG (with OCR conversion to PDF)
- **Word Documents**: DOCX
- **Markdown**: MD

---

## Rate Limiting

Currently, there is no rate limiting. Future versions will include rate limiting per API key.

---

## Best Practices

1. **Project IDs**: Use alphanumeric project IDs only (e.g., `project123`, `mybook2024`)
2. **File Sizes**: Keep files under 10 MB for optimal performance
3. **Chunk Sizes**: 
   - Small chunks (100-500): Better for precise retrieval
   - Medium chunks (500-1000): Balanced approach
   - Large chunks (1000+): Better for context preservation
4. **Error Handling**: Always check the `signal` field in responses
5. **File IDs**: Store the `file_id` returned from upload for processing

---

## Future Endpoints (Planned)

### Image Upload with OCR
```
POST /images/upload/{project_id}
```

### Chat with Document
```
POST /chat/{project_id}
```

### Get Chat History
```
GET /chat/{project_id}/history
```

### Get Project Details
```
GET /projects/{project_id}
```

### List All Projects
```
GET /projects
```

---

## Examples

### Complete Workflow

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"
PROJECT_ID = "myproject123"

# 1. Upload document
with open('document.pdf', 'rb') as f:
    upload_response = requests.post(
        f"{BASE_URL}/data/upload/{PROJECT_ID}",
        files={'file': f}
    )
    upload_data = upload_response.json()
    print(f"Upload: {upload_data}")
    
    if upload_data.get('signal') == 'File uploaded successfully.':
        file_id = upload_data['file_id']
        
        # 2. Process document
        process_response = requests.post(
            f"{BASE_URL}/data/process/{PROJECT_ID}",
            json={
                'file_id': file_id,
                'chunk_size': 1000,
                'overlap_size': 200
            }
        )
        process_data = process_response.json()
        print(f"Process: {process_data}")
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = 'http://localhost:5000/api/v1';
const PROJECT_ID = 'myproject123';

// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch(
  `${BASE_URL}/data/upload/${PROJECT_ID}`,
  {
    method: 'POST',
    body: formData
  }
);
const uploadData = await uploadResponse.json();

if (uploadData.signal === 'File uploaded successfully.') {
  // Process document
  const processResponse = await fetch(
    `${BASE_URL}/data/process/${PROJECT_ID}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_id: uploadData.file_id,
        chunk_size: 1000,
        overlap_size: 200
      })
    }
  );
  const processData = await processResponse.json();
  console.log(processData);
}
```

---

## Testing

You can test the API using:
- **Swagger UI**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`
- **cURL**: Command-line tool
- **Postman**: API testing tool
- **Python requests**: As shown in examples

---

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue on GitHub
- Contact the maintainers


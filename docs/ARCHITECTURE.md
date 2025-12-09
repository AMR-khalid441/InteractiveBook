# Architecture Documentation

## System Overview

InteractiveBook is built using a modern microservices-inspired architecture with clear separation of concerns. The system follows a layered architecture pattern with async/await support throughout for high performance.

---

## Architecture Layers

### 1. Presentation Layer (Frontend - Planned)
- **Technology**: React 18+ with TypeScript
- **State Management**: Zustand (planned)
- **Styling**: Tailwind CSS (planned)
- **Build Tool**: Vite (planned)

**Responsibilities:**
- User interface rendering
- User interaction handling
- API communication
- State management

### 2. API Layer (Backend)
- **Technology**: FastAPI 0.121.0
- **Pattern**: RESTful API
- **Async**: Full async/await support

**Location**: `src/routes/`

**Components:**
- `base.py`: Base router with welcome endpoint
- `data_router.py`: Document upload and processing endpoints

**Responsibilities:**
- Request routing
- Request validation (Pydantic)
- Response formatting
- Error handling

### 3. Business Logic Layer (Controllers)
- **Location**: `src/controllers/`

**Components:**
- `BaseController.py`: Base controller with common functionality
- `DataController.py`: File validation and path management
- `ProcessController.py`: Text chunking and processing
- `ProjectController.py`: Project path management

**Responsibilities:**
- Business logic implementation
- File validation
- Text processing
- Path management

### 4. Data Access Layer (Models)
- **Location**: `src/models/`

**Components:**
- `BaseDataModel.py`: Base model for database operations
- `ProjectModel.py`: MongoDB operations for projects
- `db_schemas/`: Pydantic models for data validation
  - `project.py`: Project schema
  - `DataChunk.py`: Data chunk schema

**Responsibilities:**
- Database operations
- Data validation
- Schema definitions

### 5. Service Layer
- **Location**: `src/services/`

**Services (Current):**
- `EmbeddingService`: Local SentenceTransformers embeddings (`all-MiniLM-L6-v2` by default)
- `VectorDBService`: ChromaDB persistence and similarity search
- `LLMService`: OpenAI chat completions (optional; disabled if API key missing)
- `RAGService`: Orchestrates retrieval + LLM generation with graceful fallback to search results
- `OCRService` / `PDFGeneratorService`: Planned

### 6. Data Storage Layer
- **MongoDB**: Metadata, chunks (including embeddings)
- **ChromaDB**: Vector embeddings storage (persistent client per project collection)
- **File System**: Document storage

---

## Data Flow

### Document Upload Flow

```
User Uploads File
    ↓
POST /api/v1/data/upload/{project_id}
    ↓
DataController.validate_uploaded_file()
    ├─ Check file type
    └─ Check file size
    ↓
ProjectModel.get_project_or_create_one()
    └─ Create/get project in MongoDB
    ↓
DataController.generate_unique_file_path()
    └─ Generate safe file path
    ↓
Save to File System (src/assets/files/{project_id}/)
    ↓
Return file_id
```

### Document Processing Flow

```
Process Request
    ↓
POST /api/v1/data/process/{project_id}
    ↓
ProcessController.get_file_content()
    ├─ Determine file type (.pdf, .txt, .docx, .md, .csv, .rtf)
    ├─ Load file using LangChain loader
    │   ├─ PyMuPDFLoader (for PDF)
    │   ├─ TextLoader (for TXT/RTF)
    │   ├─ UnstructuredWordDocumentLoader (DOCX)
    │   ├─ UnstructuredMarkdownLoader (MD)
    │   └─ CSVLoader (CSV)
    └─ Return document content
    ↓
ProcessController.process_file_content()
    ├─ RecursiveCharacterTextSplitter
    ├─ Split into chunks
    └─ Add metadata
    ↓
EmbeddingService.generate_embeddings_batch()
    └─ Local SentenceTransformers embeddings
    ↓
VectorDBService.add_chunks() → ChromaDB
ChunkModel.save_chunks()     → MongoDB
    ↓
Return counts + storage stats
```

### Future: Image OCR Flow

```
User Uploads Image
    ↓
POST /api/v1/images/upload/{project_id}
    ↓
OCRController.validate_image()
    ↓
OCRService.extract_text_from_image()
    ├─ EasyOCR processing
    └─ Extract text
    ↓
PDFGeneratorService.image_to_pdf()
    └─ Convert to PDF
    ↓
[Continue with Document Processing Flow]
```

### RAG Query Flow

```
User Query
    ↓
POST /api/v1/chat/{project_id}
    ↓
RAGService.generate_answer()
    ├─ EmbeddingService.generate_embedding(query)
    ├─ VectorDBService.search_similar() in ChromaDB
    ├─ Build prompt with retrieved chunks
    ├─ LLMService.generate_response() (if API key configured)
    └─ Graceful fallback: return search results if LLM unavailable
    ↓
Return Answer + Sources (or search results only)
```

---

## Database Schema

### MongoDB Collections

#### projects
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "project_id": "project123"
}
```

**Indexes:**
- `project_id` (unique)

**Operations:**
- `create_project()`: Create new project
- `get_project_or_create_one()`: Get or create project
- `get_all_projects()`: List all projects with pagination

#### chunks
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "chunk_text": "Document text content...",
  "chunk_order": 1,
  "chunk_project_id": ObjectId("507f1f77bcf86cd799439011"),
  "file_id": "abc123_document.pdf",
  "metadata": {},
  "embedding": [0.123, -0.456, ...]
}
```

**Indexes:**
- `chunk_project_id`
- `chunk_order`

#### chat_history (Planned)
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439013"),
  "project_id": "project123",
  "conversation_id": "conv_123",
  "messages": [
    {
      "role": "user",
      "content": "What is AI?",
      "timestamp": ISODate("2024-01-01T12:00:00Z")
    },
    {
      "role": "assistant",
      "content": "AI is...",
      "timestamp": ISODate("2024-01-01T12:00:05Z")
    }
  ]
}
```

### ChromaDB Structure

- **Collection per Project**: `project_{project_id}`
- **Document Format**:
  ```python
  {
    "id": "chunk_{book_id}_{chunk_order}",
    "embedding": [0.123, -0.456, ...],  # 384-dim vector by default
    "metadata": {
      "chunk_order": 1,
      "book_id": "string",
      "project_id": "string"
    }
  }
  ```

---

## File System Structure

```
src/assets/
└── files/
    └── {project_id}/
        ├── {random_string}_{clean_filename}.pdf
        ├── {random_string}_{clean_filename}.txt
        └── ...
```

**File Naming:**
- Random string prefix for uniqueness
- Cleaned original filename (special chars removed)
- Format: `{random}_{clean_filename}.{ext}`

**Security:**
- Path traversal prevention
- Filename sanitization
- Project isolation

---

## Technology Choices

### FastAPI
- **Why**: High performance, async support, automatic API docs
- **Benefits**: Fast, modern, type hints, Pydantic integration

### MongoDB
- **Why**: Flexible schema, document storage, async driver (Motor)
- **Benefits**: Easy to scale, JSON-like documents, good for metadata

### LangChain
- **Why**: Standardized document loading and text splitting
- **Benefits**: Multiple loader support, consistent API, extensible

### PyMuPDF (fitz)
- **Why**: Fast PDF processing, text extraction
- **Benefits**: Better than pdfminer for performance

### ChromaDB
- **Why**: Lightweight, embeddable, easy to use
- **Benefits**: No separate server needed, Python-native persistent client

### SentenceTransformers
- **Why**: Local, free embeddings (`all-MiniLM-L6-v2`)
- **Benefits**: Fast, CPU-friendly by default, no external API required

### OpenAI API
- **Why**: High-quality LLM responses for chat
- **Benefits**: Production-ready, reliable; optional so search still works without a key

---

## Security Considerations

### File Upload Security
- ✅ File type validation (whitelist)
- ✅ File size limits (10 MB)
- ✅ Path traversal prevention
- ✅ Filename sanitization
- ✅ Project isolation

### API Security
- ✅ Input validation (Pydantic)
- ✅ Error message sanitization
- ⏳ Rate limiting (planned)
- ⏳ Authentication (planned)
- ⏳ API key management (planned)

### Data Security
- ✅ Environment variable management
- ⏳ API key encryption (planned)
- ⏳ Database connection security
- ⏳ HTTPS enforcement (production)

---

## Performance Optimizations

### Backend
- ✅ Async/await for I/O operations
- ✅ Connection pooling (MongoDB Motor)
- ✅ Batch embedding generation for chunk sets
- ⏳ Caching (Redis - planned)
- ⏳ Background job processing (Celery - planned)

### Frontend (Planned)
- Code splitting
- Lazy loading
- React Query for data fetching
- Optimistic updates

---

## Scalability

### Horizontal Scaling
- ✅ Stateless API design
- ✅ Load balancer ready
- ✅ Database connection pooling
- ⏳ Vector DB sharding (planned)
- ⏳ File storage (S3/GCS - planned)

### Vertical Scaling
- ✅ Async processing
- ✅ Efficient memory usage
- ⏳ Background job processing (planned)
- ⏳ Streaming responses (planned)

---

## Error Handling

### Backend Error Handling
- ✅ Try-except blocks in controllers
- ✅ Centralized error responses
- ✅ Logging with proper levels
- ✅ User-friendly error messages
- ⏳ Error tracking (Sentry - planned)

### Error Response Format
```json
{
  "signal": "Error message",
  "error": "Detailed error description (optional)"
}
```

---

## Logging

### Current Implementation
- Uses Python `logging` module
- Uvicorn error logger
- Error logging in controllers

### Planned Improvements
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging middleware
- Centralized log aggregation

---

## Testing Strategy

### Current State
- Manual testing
- API testing via Swagger UI

### Planned Testing
- **Unit Tests**: Controllers, models, utilities
- **Integration Tests**: API endpoints
- **Database Tests**: MongoDB operations
- **Service Tests**: OCR, embedding, RAG services
- **E2E Tests**: Complete workflows

---

## Deployment Architecture

### Development
```
Local Machine
├── FastAPI (localhost:5000)
├── MongoDB (Docker)
├── ChromaDB (Local)
└── React (localhost:3000) - planned
```

### Production (AWS)
```
AWS Cloud
├── Application Load Balancer
├── ECS/EC2 (FastAPI)
├── RDS/MongoDB Atlas
├── S3 (File Storage)
├── CloudFront (CDN)
└── Route 53 (DNS)
```

### Production (GCP)
```
GCP Cloud
├── Cloud Load Balancer
├── Cloud Run (FastAPI)
├── Cloud SQL/MongoDB Atlas
├── Cloud Storage
└── Cloud CDN
```

---

## Future Architecture Improvements

1. **Microservices**: Split into separate services (upload, process, chat)
2. **Message Queue**: Use RabbitMQ/Kafka for async processing
3. **Caching Layer**: Redis for frequently accessed data
4. **CDN**: CloudFront/CloudFlare for static assets
5. **Monitoring**: Prometheus + Grafana
6. **Tracing**: OpenTelemetry for distributed tracing
7. **API Gateway**: Kong/AWS API Gateway for routing

---

## Diagrams

### Component Diagram
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   FastAPI App   │
│  ┌───────────┐  │
│  │  Routes   │  │
│  └─────┬─────┘  │
│  ┌─────▼─────┐  │
│  │Controllers│  │
│  └─────┬─────┘  │
│  ┌─────▼─────┐  │
│  │  Models   │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│MongoDB │ │File Sys │
└────────┘ └──────────┘
```

### Sequence Diagram (Upload & Process)
```
User    API     Controller    Model      MongoDB    FileSystem
 │       │          │           │           │            │
 │──POST─>│          │           │           │            │
 │       │──validate>│           │           │            │
 │       │<──valid──│           │           │            │
 │       │──get/create──────────>│           │            │
 │       │          │           │──query───>│            │
 │       │          │           │<──result──│            │
 │       │<──project────────────│           │            │
 │       │──save───────────────────────────────────────>│
 │       │<──file_id────────────────────────────────────│
 │<──200──│          │           │           │            │
 │       │          │           │           │            │
 │──POST─>│          │           │           │            │
 │       │──process─>│           │           │            │
 │       │          │──load─────────────────────────────>│
 │       │          │<──content──────────────────────────│
 │       │          │──chunk───>│           │            │
 │       │<──chunks─│           │           │            │
 │<──200──│          │           │           │            │
```

---

For deployment details, see [DEPLOYMENT.md](DEPLOYMENT.md).


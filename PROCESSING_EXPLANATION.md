# PDF Processing Flow - What Happens When You Process a PDF

## Overview
When you call `/api/v1/data/process/{project_id}`, the system performs the following steps:

### Step 1: File Upload (Already Done)
- File is uploaded via `/api/v1/data/upload/{project_id}`
- File is saved to disk at: `src/assets/files/{project_id}/{random_string}_{filename}.pdf`
- Returns a `file_id` like: `73peyf29g5ep_AIengineerupdated.pdf`

### Step 2: Processing Request
You send a POST request to `/api/v1/data/process/{project_id}` with:
```json
{
  "file_id": "73peyf29g5ep_AIengineerupdated.pdf",
  "chunk_size": 1000,
  "overlap_size": 200,
  "do_reset": 0
}
```

### Step 3: What Processing Actually Does

#### 3.1 File Loading
- **Uses PyMuPDFLoader** (LangChain wrapper around PyMuPDF/fitz library)
- Extracts text from each page of the PDF
- Returns a list of Document objects, one per page
- Each Document has:
  - `page_content`: The extracted text
  - `metadata`: Page number, source file, etc.

#### 3.2 Text Chunking
- **Uses RecursiveCharacterTextSplitter** (LangChain)
- Splits the text into smaller chunks of size `chunk_size` (default 1000 characters)
- Overlaps chunks by `overlap_size` (default 200 characters) to preserve context
- Creates multiple chunks from the document

#### 3.3 Embedding Generation
- **Uses Sentence Transformers** (local model: `all-MiniLM-L6-v2`)
- Generates vector embeddings for each chunk
- Each embedding is a 384-dimensional vector representing the semantic meaning
- Embeddings are stored with each chunk

#### 3.4 Database Storage
- Saves chunks to MongoDB collection: `chunks`
- Each chunk document contains:
  - `chunk_text`: The actual text content
  - `chunk_project_id`: Reference to the project
  - `file_id`: Reference to the source file
  - `embedding`: The vector embedding (384 floats)
  - `metadata`: Additional information (page number, etc.)

### Step 4: Response
Returns:
```json
{
  "signal": "process success",
  "chunks_count": 150,
  "saved_count": 150,
  "embeddings_generated": 150
}
```

## Common Failure Points

### 1. File Not Found (400 Bad Request)
- **Cause**: File doesn't exist at expected path
- **Check**: Verify file was uploaded successfully
- **Solution**: Re-upload the file

### 2. Unsupported File Type (400 Bad Request)
- **Cause**: File extension doesn't match supported types
- **Supported**: `.pdf`, `.txt`, `.docx`, `.md`, `.csv`, `.rtf`
- **Solution**: Check file extension is correct

### 3. PDF Loading Error (400 Bad Request)
- **Cause**: PDF is corrupted, password-protected, or image-based (no text)
- **Check**: Try opening PDF in a PDF viewer
- **Solution**: 
  - If password-protected: Remove password
  - If image-based: Use OCR (not yet implemented)
  - If corrupted: Re-save the PDF

### 4. Empty File (400 Bad Request)
- **Cause**: PDF contains no extractable text
- **Solution**: PDF might be image-only, needs OCR

### 5. No Chunks Created (400 Bad Request)
- **Cause**: Text splitter couldn't create chunks
- **Solution**: Check if file has any text content

## Dependencies Required

- **PyMuPDF**: For PDF text extraction
- **LangChain**: For document loading and text splitting
- **Sentence Transformers**: For embedding generation
- **MongoDB**: For storing chunks and embeddings

## Debugging

Check the terminal logs for detailed error messages. The system now logs:
- File path being checked
- File extension detected
- Loader type being used
- Number of documents/pages extracted
- Number of chunks created
- Any errors with full stack traces


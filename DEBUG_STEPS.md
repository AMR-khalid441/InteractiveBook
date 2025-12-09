# Debug Steps for PDF Processing Error

## Step 1: Check What Error You're Getting

When you make the request, check:
1. **HTTP Status Code** (400, 422, 500?)
2. **Response Body** - Copy the entire JSON response
3. **Terminal Logs** - Copy all the log messages from the terminal

## Step 2: Test File Upload

First, make sure the file was uploaded successfully:

```bash
POST http://localhost:5000/api/v1/data/upload/1
Content-Type: multipart/form-data
Body: file=@yourfile.pdf
```

**Check the response:**
- Should return `file_id` like: `73peyf29g5ep_AIengineerupdated.pdf`
- Copy this EXACT `file_id` (no spaces, no commas)

## Step 3: List Files (Debug Endpoint)

Use the new debug endpoint to see what files actually exist:

```bash
GET http://localhost:5000/api/v1/data/debug/files/1
```

This will show:
- All files in the project directory
- The exact file paths
- File count

## Step 4: Test Processing

Use the EXACT `file_id` from Step 2:

```json
POST http://localhost:5000/api/v1/data/process/1
Content-Type: application/json

{
  "file_id": "73peyf29g5ep_AIengineerupdated.pdf",
  "chunk_size": 1000,
  "overlap_size": 200,
  "do_reset": 0
}
```

## Step 5: Check Terminal Logs

The terminal should now show detailed logs like:

```
INFO: === PROCESS REQUEST RECEIVED ===
INFO: Project ID: '1'
INFO: Processing file_id: '73peyf29g5ep_AIengineerupdated.pdf'
INFO: Looking for file at: D:\Corsat\InteractiveBook\src\assets\files\1\73peyf29g5ep_AIengineerupdated.pdf
INFO: Getting file content for: 73peyf29g5ep_AIengineerupdated.pdf
INFO: File extension detected: .pdf
INFO: Loader created: PyMuPDFLoader
INFO: File loaded successfully: 10 documents/pages extracted
```

## Step 6: Confirm Vector Storage

- Check logs for `Generated X embeddings` and `Stored X chunks in ChromaDB`
- If embeddings fail, chunks are still saved to MongoDB but search/chat relevance will suffer

## Common Issues

### Issue 1: File Not Found
**Error Response:**
```json
{
  "signal": "process failed",
  "error": "File not found: ...",
  "file_path": "...",
  "available_files": [...]
}
```

**Solution:**
- Check the `available_files` list
- Make sure the `file_id` matches exactly
- Re-upload the file if needed

### Issue 2: 422 Unprocessable Entity
**This means the request body is invalid**

**Solution:**
- Check JSON syntax (no trailing commas)
- Make sure `file_id` is a string (in quotes)
- Verify all required fields are present

### Issue 3: PDF Loading Error
**Error Response:**
```json
{
  "signal": "process failed",
  "error": "Error loading PDF file: ...",
  "error_type": "..."
}
```

**Possible Causes:**
- PDF is corrupted
- PDF is password-protected
- PDF is image-only (no text)
- PyMuPDF library issue

**Solution:**
- Try opening PDF in a PDF viewer
- Try a different PDF file
- Check if PDF has extractable text

### Issue 4: Chat returns only search results
- **Cause:** `OPENAI_API_KEY` missing/invalid or OpenAI call failed
- **Solution:** Add a valid API key to `src/assets/.env`, restart the server, and retry

## What to Share

If it still doesn't work, share:
1. **Exact error response** (copy the full JSON)
2. **Terminal logs** (all the INFO/ERROR messages)
3. **The file_id** you're using
4. **The file_id** from the upload response


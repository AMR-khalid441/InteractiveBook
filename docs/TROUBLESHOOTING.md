# Troubleshooting Guide

Common issues and solutions for InteractiveBook.

---

## Table of Contents

1. [Setup Issues](#setup-issues)
2. [MongoDB Issues](#mongodb-issues)
3. [File Upload Issues](#file-upload-issues)
4. [API Errors](#api-errors)
5. [Performance Issues](#performance-issues)
6. [Deployment Issues](#deployment-issues)

---

## Setup Issues

### Python Version Error

**Error:**
```
Python 3.10+ is required
```

**Solution:**
1. Check Python version:
   ```bash
   python --version
   ```
2. Install Python 3.10+ if needed
3. Use correct Python version:
   ```bash
   python3.10 -m venv venv
   ```

### Virtual Environment Not Activating

**Error:**
```
'venv\Scripts\activate' is not recognized
```

**Solutions:**

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
# If blocked, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Module Installation Fails

**Error:**
```
ERROR: Could not install packages
```

**Solutions:**
1. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```
2. Use virtual environment
3. Check internet connection
4. Try installing individually:
   ```bash
   pip install fastapi
   pip install uvicorn
   ```

### Environment Variables Not Loading

**Error:**
```
KeyError: 'OPENAI_API_KEY'
```

**Solutions:**
1. Verify `.env` file exists in `src/assets/`
2. Check file format (no spaces around `=`):
   ```env
   OPENAI_API_KEY=sk-...  # Correct
   OPENAI_API_KEY = sk-...  # Wrong
   ```
3. Verify file path in `config.py`
4. Restart the application
5. Check file permissions

---

## MongoDB Issues

### Connection Refused

**Error:**
```
ServerSelectionTimeoutError: localhost:27017
[WinError 10061] No connection could be made
```

**Solutions:**

1. **Check if MongoDB is running:**
   ```bash
   docker ps
   ```

2. **Start MongoDB:**
   ```bash
   cd docker
   docker-compose up -d mongodb
   ```

3. **Check MongoDB logs:**
   ```bash
   docker logs mongodb
   ```

4. **Verify connection string:**
   ```env
   MONGODB_URl=mongodb://localhost:27017
   ```

5. **Test connection:**
   ```bash
   docker exec -it mongodb mongosh
   ```

### Authentication Failed

**Error:**
```
Authentication failed
```

**Solutions:**
1. Check username/password in connection string
2. Verify MongoDB user exists
3. Check IP whitelist (for MongoDB Atlas)
4. Verify database name

### Database Not Found

**Error:**
```
Database not found
```

**Solution:**
- Database is created automatically on first use
- Verify `MONGODB_DB_NAME` in `.env`
- Check MongoDB connection

### Port Already in Use

**Error:**
```
Port 27017 is already in use
```

**Solutions:**
1. **Find process using port:**
   ```bash
   # Windows
   netstat -ano | findstr :27017
   
   # Mac/Linux
   lsof -i :27017
   ```

2. **Kill the process** or change MongoDB port in `docker-compose.yml`

3. **Stop existing MongoDB:**
   ```bash
   docker stop mongodb
   ```

---

## File Upload Issues

### File Type Not Supported

**Error:**
```json
{
  "signal": "File type not supported."
}
```

**Solutions:**
1. Check file type is in allowed list:
   ```env
   FILE_ALLOWED_EXTENSIONS=["application/pdf","text/plain"]
   ```
2. Verify file extension matches MIME type
3. Check file is not corrupted
4. Add new file type to `FILE_ALLOWED_EXTENSIONS` if needed

### File Size Exceeded

**Error:**
```json
{
  "signal": "File size exceeded the maximum limit."
}
```

**Solutions:**
1. Check file size:
   ```bash
   ls -lh file.pdf
   ```
2. Increase limit in `.env`:
   ```env
   FILE_MAX_SIZE=20971520  # 20 MB
   ```
3. Compress or split large files

### Upload Fails Silently

**Symptoms:**
- No error message
- File not saved

**Solutions:**
1. Check disk space:
   ```bash
   df -h  # Mac/Linux
   ```
2. Verify write permissions:
   ```bash
   ls -la src/assets/files/
   ```
3. Check application logs
4. Verify file path exists:
   ```bash
   ls src/assets/files/
   ```

### Path Traversal Attempt

**Error:**
```
Invalid file path
```

**Solution:**
- File paths are sanitized automatically
- Use only alphanumeric project IDs
- Don't use `../` in filenames

---

## API Errors

### 404 Not Found

**Error:**
```
404: Not Found
```

**Solutions:**
1. Check endpoint URL:
   ```
   http://localhost:5000/api/v1/data/upload/project123
   ```
2. Verify route exists in `routes/`
3. Check API prefix: `/api/v1`
4. Ensure server is running

### 500 Internal Server Error

**Error:**
```json
{
  "signal": "process failed",
  "error": "..."
}
```

**Solutions:**
1. Check application logs:
   ```bash
   # If running with uvicorn
   # Check terminal output
   ```
2. Verify environment variables
3. Check database connection
4. Verify file exists before processing
5. Check file permissions

### Validation Error

**Error:**
```
422: Unprocessable Entity
```

**Solutions:**
1. Check request body format
2. Verify required fields are present
3. Check data types match schema
4. Review API documentation: [API.md](API.md)

### Chat returns only search results

**Symptom:**
- Chat endpoint responds with `answer: null` and returns `search_results` + `warning`

**Solutions:**
1. Set `OPENAI_API_KEY` in `src/assets/.env`
2. Restart the FastAPI server after updating `.env`
3. Check logs for OpenAI errors (rate limits, invalid key)

### CORS Error (Frontend)

**Error:**
```
CORS policy: No 'Access-Control-Allow-Origin'
```

**Solutions:**
1. Add CORS middleware in `main.py`:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Configure appropriately
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## Performance Issues

### Slow File Processing

**Symptoms:**
- Processing takes too long
- Timeout errors

**Solutions:**
1. **Reduce chunk size:**
   ```json
   {
     "chunk_size": 500,
     "overlap_size": 50
   }
   ```
2. **Optimize file size** (compress PDFs)
3. **Use async processing** (background jobs)
4. **Increase timeout** in production

### High Memory Usage

**Symptoms:**
- Application crashes
- Out of memory errors

**Solutions:**
1. Process files in chunks
2. Use streaming for large files
3. Increase server memory
4. Optimize chunk sizes

### Database Slow Queries

**Solutions:**
1. Add indexes:
   ```python
   # In MongoDB
   db.projects.create_index("project_id")
   ```
2. Optimize queries
3. Use connection pooling
4. Consider database upgrade

---

## Deployment Issues

### Docker Build Fails

**Error:**
```
ERROR: failed to solve
```

**Solutions:**
1. Check Dockerfile syntax
2. Verify base image exists
3. Check network connection
4. Clear Docker cache:
   ```bash
   docker system prune -a
   ```

### Container Won't Start

**Error:**
```
Container exited with code 1
```

**Solutions:**
1. Check container logs:
   ```bash
   docker logs container-name
   ```
2. Verify environment variables
3. Check file permissions
4. Verify dependencies installed

### Port Conflicts

**Error:**
```
Port is already allocated
```

**Solutions:**
1. Find process using port
2. Change port in configuration
3. Stop conflicting service

### Environment Variables Not Set

**Error:**
```
Environment variable not found
```

**Solutions:**
1. Check `.env` file exists
2. Verify variable names match
3. Use `docker-compose` environment section
4. Check secrets management (cloud platforms)

---

## Common Error Messages

### TypeError: object NoneType can't be used in 'await'

**Cause:** MongoDB connection is None

**Solution:**
- Check MongoDB is running
- Verify connection string
- Ensure startup event completed

### UnboundLocalError: cannot access local variable

**Cause:** Variable shadowing

**Solution:**
- Rename local variables to avoid conflicts
- Check variable scope

### PydanticSchemaGenerationError

**Cause:** Pydantic v2 compatibility issue

**Solution:**
- Use `model_config = ConfigDict(...)` instead of `class config`
- Check `arbitrary_types_allowed` spelling

### ModuleNotFoundError

**Cause:** Import path issue

**Solution:**
- Use relative imports: `from .module import Class`
- Check `__init__.py` files exist
- Verify package structure

---

## Getting More Help

### Debug Mode

Enable debug logging:
```bash
uvicorn main:app --reload --log-level debug
```

### Check Logs

**Application logs:**
- Check terminal output
- Check log files (if configured)

**Docker logs:**
```bash
docker logs mongodb
docker logs interactivebook
```

**System logs:**
```bash
# Linux
journalctl -u interactivebook

# Mac
log show --predicate 'process == "uvicorn"'
```

### Enable Verbose Output

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Components Individually

1. **Test MongoDB:**
   ```bash
   docker exec -it mongodb mongosh
   use interactivebook
   db.projects.find()
   ```

2. **Test API:**
   ```bash
   curl http://localhost:5000/api/v1/welcome
   ```

3. **Test file upload:**
   ```bash
   curl -X POST "http://localhost:5000/api/v1/data/upload/test" \
     -F "file=@test.pdf"
   ```

---

## Prevention Tips

1. **Always use virtual environments**
2. **Keep dependencies updated**
3. **Test in development before production**
4. **Monitor logs regularly**
5. **Backup data regularly**
6. **Use environment variables for secrets**
7. **Validate inputs**
8. **Handle errors gracefully**

---

## Still Need Help?

1. **Check documentation:**
   - [SETUP.md](SETUP.md)
   - [API.md](API.md)
   - [ARCHITECTURE.md](ARCHITECTURE.md)

2. **Search existing issues** on GitHub

3. **Create a new issue** with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Logs (if applicable)

4. **Contact maintainers**

---

**Remember:** Most issues are resolved by checking logs, verifying configuration, and ensuring all services are running.


# Setup Guide

Complete step-by-step instructions for setting up InteractiveBook on your local machine.

---

## Prerequisites

### Required Software

1. **Python 3.10 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`
   - On Windows, check "Add Python to PATH" during installation

2. **Docker & Docker Compose**
   - Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Verify installation:
     ```bash
     docker --version
     docker-compose --version
     ```

3. **Git**
   - Download from [git-scm.com](https://git-scm.com/downloads)
   - Verify installation: `git --version`

4. **OpenAI API Key**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Create an API key from the dashboard
   - Keep it secure (you'll need it for configuration)

### Optional Software

- **VS Code** or your preferred IDE
- **Postman** or **Insomnia** for API testing
- **MongoDB Compass** for database visualization

---

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/InteractiveBook.git
cd InteractiveBook
```

### Step 2: Set Up MongoDB with Docker

1. **Navigate to docker directory**
   ```bash
   cd docker
   ```

2. **Start MongoDB container**
   ```bash
   docker-compose up -d mongodb
   ```

3. **Verify MongoDB is running**
   ```bash
   docker ps
   ```
   You should see a container named `mongodb` running.

4. **Test MongoDB connection** (optional)
   ```bash
   docker exec -it mongodb mongosh
   ```
   Then in MongoDB shell:
   ```javascript
   show dbs
   exit
   ```

### Step 3: Set Up Python Virtual Environment

**Windows:**
```bash
cd ..
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
cd ..
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Verify installation:**
```bash
pip list
```

You should see packages like `fastapi`, `uvicorn`, `motor`, `pydantic`, etc.

### Step 5: Configure Environment Variables

1. **Navigate to assets directory**
   ```bash
   cd src/assets
   ```

2. **Create `.env` file**
   
   **Windows (PowerShell):**
   ```powershell
   New-Item -Path .env -ItemType File
   ```
   
   **Mac/Linux:**
   ```bash
   touch .env
   ```

3. **Add the following content to `.env`:**

   ```env
   APPLICATION_NAME=InteractiveBook
   APP_VERSION=1.0.0
   OPENAI_API_KEY=your_openai_api_key_here
   FILE_ALLOWED_EXTENSIONS=["application/pdf","text/plain"]
   FILE_MAX_SIZE=10485760
   FILE_CHUNK_SIZE=512000
   MONGODB_URl=mongodb://localhost:27017
   MONGODB_DB_NAME=interactivebook
   ```

4. **Replace `your_openai_api_key_here` with your actual OpenAI API key**

   **Important**: Never commit the `.env` file to version control!

### Step 6: Verify File Structure

Your project structure should look like this:

```
InteractiveBook/
├── src/
│   ├── assets/
│   │   ├── .env          ← Should exist
│   │   └── files/        ← Will be created automatically
│   ├── controllers/
│   ├── helpers/
│   ├── models/
│   ├── routes/
│   └── main.py
├── docker/
│   └── docker-compose.yml
├── requirements.txt
└── README.md
```

### Step 7: Run the Application

1. **Navigate to src directory**
   ```bash
   cd src
   ```

2. **Start the FastAPI server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 5000
   ```

   You should see output like:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

3. **Verify the API is running**
   
   Open your browser and visit:
   - API: `http://localhost:5000/api/v1/welcome`
   - Swagger UI: `http://localhost:5000/docs`
   - ReDoc: `http://localhost:5000/redoc`

---

## Platform-Specific Instructions

### Windows

#### PowerShell Setup
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt

# Start MongoDB
cd docker
docker-compose up -d mongodb
cd ..

# Run application
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

#### Command Prompt Setup
```cmd
# Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Start MongoDB
cd docker
docker-compose up -d mongodb
cd ..

# Run application
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### Mac

```bash
# Install Python if needed
brew install python@3.10

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB
cd docker
docker-compose up -d mongodb
cd ..

# Run application
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Docker (if not installed)
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB
cd docker
docker-compose up -d mongodb
cd ..

# Run application
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

---

## Configuration Details

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APPLICATION_NAME` | Application name | `InteractiveBook` | No |
| `APP_VERSION` | Application version | `1.0.0` | No |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `FILE_ALLOWED_EXTENSIONS` | Allowed file types | `["application/pdf","text/plain"]` | No |
| `FILE_MAX_SIZE` | Max file size in bytes | `10485760` (10 MB) | No |
| `FILE_CHUNK_SIZE` | File upload chunk size | `512000` (500 KB) | No |
| `MONGODB_URl` | MongoDB connection string | `mongodb://localhost:27017` | Yes |
| `MONGODB_DB_NAME` | MongoDB database name | `interactivebook` | No |

### MongoDB Connection String

**Local MongoDB (Docker):**
```
MONGODB_URl=mongodb://localhost:27017
```

**MongoDB Atlas (Cloud):**
```
MONGODB_URl=mongodb+srv://username:password@cluster.mongodb.net/
```

**MongoDB with Authentication:**
```
MONGODB_URl=mongodb://username:password@localhost:27017
```

---

## Testing the Setup

### 1. Test API Health

```bash
curl http://localhost:5000/api/v1/welcome
```

Expected response:
```json
{
  "status": "running",
  "name": "InteractiveBook",
  "version": "1.0.0",
  "open_api_key": "sk-..."
}
```

### 2. Test File Upload

Create a test PDF or text file, then:

```bash
curl -X POST "http://localhost:5000/api/v1/data/upload/testproject" \
  -F "file=@test.pdf"
```

Expected response:
```json
{
  "signal": "File uploaded successfully.",
  "file_id": "abc123_test.pdf",
  "project_id": "..."
}
```

### 3. Test Document Processing

```bash
curl -X POST "http://localhost:5000/api/v1/data/process/testproject" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "abc123_test.pdf",
    "chunk_size": 100,
    "overlap_size": 20
  }'
```

Expected response:
```json
{
  "signal": "process success",
  "chunks_count": 10
}
```

---

## Common Setup Issues

### Issue: MongoDB Connection Failed

**Symptoms:**
```
ServerSelectionTimeoutError: localhost:27017
```

**Solutions:**
1. Check if MongoDB is running:
   ```bash
   docker ps
   ```
2. Start MongoDB if not running:
   ```bash
   cd docker
   docker-compose up -d mongodb
   ```
3. Check MongoDB logs:
   ```bash
   docker logs mongodb
   ```

### Issue: Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
1. Ensure virtual environment is activated (you should see `(venv)` in prompt)
2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Issue: Port Already in Use

**Symptoms:**
```
ERROR: [Errno 48] Address already in use
```

**Solutions:**
1. Find process using port 5000:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   
   # Mac/Linux
   lsof -i :5000
   ```
2. Kill the process or use a different port:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Issue: Environment Variables Not Loading

**Symptoms:**
```
KeyError: 'OPENAI_API_KEY'
```

**Solutions:**
1. Verify `.env` file exists in `src/assets/`
2. Check file path in `config.py`:
   ```python
   env_file = os.path.join(os.path.dirname(__file__), "../assets/.env")
   ```
3. Ensure `.env` file has correct format (no spaces around `=`)
4. Restart the application

### Issue: File Upload Fails

**Symptoms:**
```
signal: "File type not supported."
```

**Solutions:**
1. Check file type is in `FILE_ALLOWED_EXTENSIONS`
2. Verify file size is under `FILE_MAX_SIZE`
3. Check file is not corrupted

---

## Next Steps

After successful setup:

1. **Read the API Documentation**: [API.md](API.md)
2. **Understand the Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Start Developing**: Check [CONTRIBUTING.md](CONTRIBUTING.md)
4. **Deploy to Production**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Development Tips

### Hot Reload

The `--reload` flag enables automatic reloading when code changes:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### Debug Mode

Enable debug logging:
```bash
uvicorn main:app --reload --log-level debug
```

### Using Different Ports

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Accessing MongoDB

**Using MongoDB Compass:**
- Connection string: `mongodb://localhost:27017`
- Database: `interactivebook`

**Using Command Line:**
```bash
docker exec -it mongodb mongosh
use interactivebook
db.projects.find()
```

---

## Uninstallation

To completely remove the setup:

1. **Stop the application** (Ctrl+C)

2. **Stop MongoDB:**
   ```bash
   cd docker
   docker-compose down
   ```

3. **Remove virtual environment:**
   ```bash
   deactivate  # Exit virtual environment
   rm -rf venv  # Mac/Linux
   rmdir /s venv  # Windows
   ```

4. **Remove MongoDB data** (optional):
   ```bash
   cd docker
   docker-compose down -v  # Removes volumes
   ```

---

## Getting Help

If you encounter issues:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review error logs
3. Check GitHub issues
4. Contact maintainers

---

**Setup complete! Happy coding! 🚀**


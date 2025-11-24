# Contributing Guidelines

Thank you for your interest in contributing to InteractiveBook! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Style](#code-style)
5. [Commit Messages](#commit-messages)
6. [Pull Request Process](#pull-request-process)
7. [Testing](#testing)
8. [Documentation](#documentation)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks

---

## Getting Started

### 1. Fork the Repository

1. Click the "Fork" button on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/InteractiveBook.git
   cd InteractiveBook
   ```

### 2. Set Up Development Environment

Follow the setup instructions in [SETUP.md](SETUP.md).

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

---

## Development Workflow

### 1. Make Changes

- Write clean, readable code
- Follow the code style guidelines
- Add comments for complex logic
- Update documentation as needed

### 2. Test Your Changes

```bash
# Run tests
pytest tests/

# Check code style
black src/ --check
isort src/ --check

# Type checking (if applicable)
mypy src/
```

### 3. Commit Your Changes

Follow the commit message guidelines below.

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template
5. Submit the PR

---

## Code Style

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications.

#### Formatting

- **Line length**: 100 characters (soft limit)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Use in multi-line structures

#### Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_` (single underscore)

#### Example

```python
from fastapi import APIRouter, UploadFile
from typing import Optional

class DataController:
    """Controller for data operations."""
    
    def __init__(self):
        self.app_settings = get_settings()
    
    def validate_uploaded_file(self, file: UploadFile) -> tuple[bool, str]:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, message)
        """
        if file.content_type not in self.app_settings.FILE_ALLOWED_EXTENSIONS:
            return False, "File type not supported"
        return True, "File validated"
```

### Code Formatting Tools

We use:
- **Black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linter (optional)

**Setup:**
```bash
pip install black isort
```

**Usage:**
```bash
# Format code
black src/
isort src/

# Check without formatting
black src/ --check
isort src/ --check
```

### Type Hints

Use type hints for function parameters and return types:

```python
from typing import Optional, List

def process_file(
    file_id: str,
    chunk_size: int = 1000,
    overlap_size: Optional[int] = None
) -> List[str]:
    """Process file and return chunks."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def upload_file(file: UploadFile, project_id: str) -> dict:
    """
    Upload a file to the specified project.
    
    Args:
        file: The file to upload
        project_id: The project identifier
        
    Returns:
        Dictionary containing upload result with keys:
        - signal: Status message
        - file_id: Unique file identifier
        - project_id: Project ID
        
    Raises:
        ValueError: If file validation fails
    """
    pass
```

---

## Commit Messages

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/updates
- `chore`: Maintenance tasks

### Examples

**Good:**
```
feat: Add image upload with OCR support

- Implement OCRService for text extraction
- Add image validation
- Convert images to PDF after OCR

Closes #123
```

**Bad:**
```
update code
```

### Guidelines

- Use imperative mood ("Add" not "Added")
- Keep subject line under 50 characters
- Capitalize first letter
- No period at end of subject
- Reference issues in footer

---

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Check code style**
5. **Update CHANGELOG.md** (if exists)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Address feedback** if requested
4. **Approval** from at least one maintainer
5. **Merge** by maintainer

---

## Testing

### Writing Tests

- Use `pytest` for testing
- Place tests in `tests/` directory
- Name test files: `test_*.py`
- Name test functions: `test_*`

### Example Test

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_upload_file():
    """Test file upload endpoint."""
    with open("test.pdf", "rb") as f:
        response = client.post(
            "/api/v1/data/upload/testproject",
            files={"file": f}
        )
    assert response.status_code == 200
    assert "file_id" in response.json()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_upload.py

# Run with verbose output
pytest -v
```

---

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Explain complex algorithms
- Include examples where helpful

### API Documentation

- Update [API.md](API.md) for new endpoints
- Include request/response examples
- Document error codes

### Architecture Documentation

- Update [ARCHITECTURE.md](ARCHITECTURE.md) for major changes
- Update diagrams if needed

---

## Project Structure

```
InteractiveBook/
├── src/
│   ├── controllers/    # Business logic
│   ├── models/         # Data models
│   ├── routes/         # API endpoints
│   ├── services/       # External services
│   └── helpers/        # Utilities
├── tests/              # Test files
├── docs/               # Documentation
└── docker/             # Docker configs
```

---

## Areas for Contribution

### High Priority

- [ ] Vector database integration (ChromaDB)
- [ ] RAG pipeline implementation
- [ ] OCR service (EasyOCR)
- [ ] Frontend development (React)
- [ ] Unit tests
- [ ] Integration tests

### Medium Priority

- [ ] API authentication
- [ ] Rate limiting
- [ ] Caching layer
- [ ] Performance optimization
- [ ] Error handling improvements

### Low Priority

- [ ] Documentation improvements
- [ ] Code refactoring
- [ ] UI/UX improvements
- [ ] Additional file format support

---

## Getting Help

- **Documentation**: Check [docs/](docs/)
- **Issues**: Search existing issues on GitHub
- **Discussions**: Use GitHub Discussions
- **Contact**: Reach out to maintainers

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md (if exists)
- Mentioned in release notes
- Credited in project documentation

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to InteractiveBook! 🚀


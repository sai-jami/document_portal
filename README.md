# Document Portal

An intelligent document analysis and comparison system powered by LLMs and RAG (Retrieval-Augmented Generation) framework.

## 🚀 Features

- **Document Analysis**: Extract structured metadata, summaries, and insights from PDF documents
- **RAG Framework**: Leverages FAISS vector database for efficient document retrieval
- **Multi-LLM Support**: Supports Google Gemini and Groq models
- **FastAPI Backend**: RESTful API with automatic documentation
- **Web Interface**: Clean, modern UI for document upload and analysis
- **Structured Output**: JSON-formatted analysis results with configurable schemas
- **Session Management**: Organized document processing with unique session IDs

## 📋 Requirements

- Python 3.10+
- Google API Key (for Gemini models and embeddings)
- Groq API Key (optional, for Groq models)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd document_portal
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Environment Setup

Create a `.env` file in the root directory:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional Configuration
ENV=local
LLM_PROVIDER=google
CONFIG_PATH=config/config.yaml
DATA_STORAGE_PATH=data/document_analysis
FAISS_BASE=faiss_index
UPLOAD_BASE=data
FAISS_INDEX_NAME=index
```

### 5. Configuration

The application uses `config/config.yaml` for model and system configuration. You can customize:

- **LLM Models**: Switch between Google Gemini and Groq models
- **Embedding Models**: Configure text embedding models
- **Retrieval Settings**: Adjust top-k retrieval parameters
- **Model Parameters**: Temperature, max tokens, etc.

## 🚀 Usage

### Starting the Application

```bash
# Start the FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### API Endpoints

#### 1. Document Analysis
```bash
POST /analyze
```

Upload a PDF file and get structured analysis:

```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

**Response Format:**
```json
{
  "analysis": {
    "Summary": ["Key point 1", "Key point 2", "..."],
    "Title": "Document Title",
    "Author": ["Author Name"],
    "DateCreated": "2024-01-01",
    "LastModifiedDate": "2024-01-01",
    "Publisher": "Publisher Name",
    "Language": "English",
    "PageCount": 10,
    "SentimentTone": "Professional"
  }
}
```

#### 2. Health Check
```bash
GET /health
```

Returns application status and service information.

### Web Interface

1. Open http://localhost:8000 in your browser
2. Click "Upload PDF" and select your document
3. Click "Run Analysis" to process the document
4. View the structured analysis results in JSON format

## 🏗️ Architecture

### Project Structure

```
document_portal/
├── api/                    # FastAPI application
│   └── main.py            # Main API endpoints
├── config/                # Configuration files
│   └── config.yaml        # Model and system configuration
├── src/                   # Core application logic
│   ├── document_analyser/ # Document analysis module
│   └── document_ingestion/# Document processing and FAISS management
├── utils/                 # Utility functions
│   ├── config_loader.py   # Configuration loading
│   ├── document_ops.py    # Document operations
│   ├── file_io.py         # File I/O utilities
│   └── model_loader.py    # LLM and embedding model loading
├── models/                # Pydantic data models
├── prompt/                # LLM prompt templates
├── logger/                # Custom logging setup
├── exceptions/            # Custom exception handling
├── templates/             # HTML templates
└── static/               # CSS and static assets
```

### Key Components

1. **DocumentAnalysis**: Core analysis engine using LLM chains
2. **DocHandler**: PDF processing and session management
3. **FaissManager**: Vector database management for RAG
4. **ModelLoader**: Dynamic LLM and embedding model loading
5. **FastAPI App**: RESTful API with CORS support

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── test_api.py           # API endpoint tests
├── test_document_analysis.py  # Analysis logic tests
├── test_document_ingestion.py # Document processing tests
└── test_utils.py         # Utility function tests
```

### Example Test

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## 🔧 Configuration

### Model Configuration

Edit `config/config.yaml` to customize models:

```yaml
llm:
  google:
    provider: "google"
    model_name: "gemini-2.0-flash"
    temperature: 0
    max_output_tokens: 2048
  
  groq:
    provider: "groq"
    model_name: "deepseek-r1-distill-llama-70b"
    temperature: 0
    max_output_tokens: 2048

embedding_model:
  provider: "google"
  model_name: "models/text-embedding-004"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini models | Required |
| `GROQ_API_KEY` | Groq API key | Required |
| `LLM_PROVIDER` | LLM provider to use | `google` |
| `ENV` | Environment mode | `local` |
| `CONFIG_PATH` | Path to config file | `config/config.yaml` |

## 📊 Monitoring and Logging

The application uses structured logging with:
- **File Logging**: Daily log files in `logs/` directory
- **Console Logging**: Real-time console output
- **JSON Format**: Structured log entries for easy parsing
- **Session Tracking**: All operations tagged with session IDs

## 🚨 Error Handling

- **Custom Exceptions**: `DocumentPortalException` with detailed error context
- **API Error Responses**: Structured error messages with HTTP status codes
- **Graceful Degradation**: Fallback mechanisms for model failures
- **Input Validation**: Pydantic models for request/response validation

## 🔒 Security Considerations

- **API Key Management**: Secure environment variable handling
- **File Upload Validation**: PDF-only uploads with size limits
- **CORS Configuration**: Configurable cross-origin settings
- **Input Sanitization**: Safe file handling and processing

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

- Set `ENV=production` in environment variables
- Use proper secrets management for API keys
- Configure reverse proxy (nginx) for static files
- Set up monitoring and health checks
- Use gunicorn for production WSGI server

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all required API keys are set in `.env`
2. **Import Errors**: Run `pip install -e .` to install the package in development mode
3. **FAISS Issues**: Install `faiss-cpu` or `faiss-gpu` depending on your system
4. **PDF Processing**: Ensure PyMuPDF is properly installed for PDF handling

### Getting Help

- Check the logs in the `logs/` directory for detailed error information
- Use the `/health` endpoint to verify system status
- Review the API documentation at `/docs` for endpoint details

## 📈 Performance Tips

- Use GPU-accelerated FAISS for large document collections
- Implement caching for frequently accessed documents
- Consider async processing for large file uploads
- Monitor memory usage with large PDF files

---

**Author**: Sai Jami  
**Version**: 0.1  
**Last Updated**: 2024

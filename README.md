# Document Q&A Application

A simple application that allows users to upload documents and ask questions about them using advanced LLM capabilities.

## Features

- Document upload and management
- Natural language Q&A about document content
- Audio input support
- Chat history tracking
- Modern, intuitive interface

## Tech Stack

- Backend: Python with FastAPI
- LLM Integration: Groq with Llama 3.2
- UI: Gradio
- Deployment: Vercel

## Prerequisites

- Python 3.8+
- Groq API Key
- Git

## Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd document-qa
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Create upload directory:

   ```bash
   mkdir uploads
   ```

## Running the Application

1. Start the backend server:

   ```bash
   uvicorn src.app.main:app --reload
   ```

2. The application will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## Usage

1. Upload a document using the sidebar
2. Select an uploaded document
3. Ask questions about the document content
4. View chat history and previous interactions

## Development

- Follow PEP 8 style guide
- Run tests: `pytest`
- Format code: `black src/`
- Check types: `mypy src/`

## License

MIT License - See LICENSE file for details

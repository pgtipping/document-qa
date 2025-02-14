import pytest
from fastapi import UploadFile, HTTPException
from app.services.document import DocumentService
import os
import tempfile
import shutil
from app.core.config import settings


@pytest.fixture
def document_service():
    # Create a temporary directory for testing
    test_upload_dir = tempfile.mkdtemp()
    settings.UPLOAD_DIR = test_upload_dir
    
    service = DocumentService()
    yield service
    
    # Cleanup after tests
    shutil.rmtree(test_upload_dir)


@pytest.fixture
def sample_file():
    content = b"Test document content"
    return UploadFile(
        filename="test.txt",
        file=tempfile.SpooledTemporaryFile()._file,
        content_type="text/plain"
    )


async def test_save_document(document_service, sample_file):
    # Test saving a valid document
    document_id = await document_service.save_document(sample_file)
    assert document_id is not None
    assert len(document_id) > 0
    
    # Verify file exists
    files = os.listdir(settings.UPLOAD_DIR)
    assert len(files) == 1
    assert files[0].startswith(document_id)


async def test_invalid_extension(document_service):
    # Test saving a file with invalid extension
    invalid_file = UploadFile(
        filename="test.invalid",
        file=tempfile.SpooledTemporaryFile()._file
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await document_service.save_document(invalid_file)
    assert exc_info.value.status_code == 400


async def test_list_documents(document_service, sample_file):
    # Save a test document
    document_id = await document_service.save_document(sample_file)
    
    # Test listing documents
    documents = await document_service.list_documents()
    assert len(documents) == 1
    assert documents[0].id == document_id
    assert documents[0].filename.endswith(".txt")
    assert documents[0].content_type == "text/plain" 
from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnum

class ProcessController(BaseController):

    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1].lower()

    def get_file_loader(self, file_id: str):

        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(
            self.project_path,
            file_id
        )

        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")

        elif file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        
        elif file_ext == ProcessingEnum.DOCX.value:
            return UnstructuredWordDocumentLoader(file_path)
        
        elif file_ext == ProcessingEnum.MD.value:
            return UnstructuredMarkdownLoader(file_path)
        
        elif file_ext == ProcessingEnum.CSV.value:
            return CSVLoader(file_path)
        
        elif file_ext == ProcessingEnum.RTF.value:
            return TextLoader(file_path, encoding="utf-8")
        
        return None

    def get_file_content(self, file_id: str):
        import logging
        logger = logging.getLogger("uvicorn.error")
        
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)
        
        logger.info(f"Getting file content for: {file_id}")
        logger.info(f"File extension detected: {file_ext}")
        logger.info(f"Full file path: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")
        
        loader = self.get_file_loader(file_id=file_id)
        if loader is None:
            supported_types = [e.value for e in ProcessingEnum]
            error_msg = f"Unsupported file type: {file_ext}. Supported types: {supported_types}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Loader created: {type(loader).__name__}")
        
        try:
            logger.info(f"Attempting to load file: {file_path}")
            documents = loader.load()
            logger.info(f"File loaded successfully: {len(documents)} documents/pages extracted")
            
            # Log first document info for debugging
            if documents and len(documents) > 0:
                first_doc = documents[0]
                logger.info(f"First document metadata: {first_doc.metadata}")
                logger.info(f"First document content length: {len(first_doc.page_content)} characters")
            
            return documents
        except FileNotFoundError as e:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"Error loading file {file_id}: {str(e)}"
            logger.error(f"{error_msg} (Exception type: {type(e).__name__})", exc_info=True)
            raise RuntimeError(error_msg) from e

    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int=1000, overlap_size: int=200):

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
        )

        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]

        chunks = text_splitter.create_documents(
            file_content_texts,
            metadatas=file_content_metadata
        )

        return chunks


    
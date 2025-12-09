# upload data 

from fastapi import FastAPI , APIRouter , UploadFile , Depends , status , Request
from fastapi.responses import JSONResponse
from helpers import get_settings , Settings 
from controllers import ProjectController , ProcessController , DataController
import os 
import aiofiles
from models import ResponseSignal
import logging
from .schemes import ProcessRequest, SearchRequest, ChatRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from services import EmbeddingService, VectorDBService, RAGService


logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(prefix="/api/v1/data" , 
                        tags= ["api " , "router"])

@data_router.get("/debug/files/{project_id}")
async def debug_list_files(request: Request, project_id: str):
    """Debug endpoint to list all files in a project"""
    try:
        process_controller = ProcessController(project_id=project_id)
        project_path = process_controller.project_path
        
        files = []
        if os.path.exists(project_path):
            files = os.listdir(project_path)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "project_id": project_id,
                "project_path": project_path,
                "path_exists": os.path.exists(project_path),
                "files": files,
                "file_count": len(files)
            }
        )
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
@data_router.post("/upload/{project_id}")
async def upload_data(request:Request, project_id:str, file:UploadFile,
                      app_settings:Settings =Depends(get_settings)):
    project_model = ProjectModel(
         db_client=request.app.db_client
    )
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    # Validate the file properties (now async and returns file_content)
    data_controller = DataController()
    is_valid, result_signal, file_content = await data_controller.validate_uploaded_file(file=file)
    
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal  # Use the actual signal from validation
            }
        )
    
    try:
        # Generate file path
        clean_file_path, file_id = data_controller.generate_unique_file_path(
            orig_file_name=file.filename or "unknown", 
            project_id=project_id
        )
        
        logger.info(f"Uploading file - Original filename: {file.filename}")
        logger.info(f"Uploading file - Generated file_id: {file_id}")
        logger.info(f"Uploading file - Full path: {clean_file_path}")
        
        # Write the pre-read file content to disk
        async with aiofiles.open(clean_file_path, "wb") as f:
            await f.write(file_content)
        
        logger.info(f"File saved successfully: {clean_file_path}")
       
    except Exception as e:
        logger.error(f"error while uploading file : {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={
                "signal": ResponseSignal.failed_file_upload.value
            }
        )
     
    return JSONResponse(
        content={
            "signal": ResponseSignal.success_file_upload.value,
            "file_id": file_id,
            "project_id": str(project._id) if project._id else project_id
        }
    )




@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id : str , process_request :ProcessRequest ):
    try:
        logger.info(f"=== PROCESS REQUEST RECEIVED ===")
        logger.info(f"Project ID: '{project_id}'")
        logger.info(f"Request body: {process_request.model_dump() if hasattr(process_request, 'model_dump') else process_request}")
        
        # Validate request
        if not hasattr(process_request, 'file_id') or process_request.file_id is None:
            logger.error("file_id is missing from request")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "file_id is required in request body"
                }
            )
        
        # Strip whitespace and clean file_id
        file_id = process_request.file_id.strip().rstrip(',')
        
        logger.info(f"Processing file_id: '{file_id}' (original: '{process_request.file_id}')")
        
        if not file_id:
            logger.error("file_id is empty after stripping")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "file_id cannot be empty"
                }
            )
        
        # Get project to obtain ObjectId
        project_model = ProjectModel(db_client=request.app.db_client)
        project = await project_model.get_project_or_create_one(project_id=project_id)
        
        if not project._id:
            logger.error(f"Invalid project: {project_id}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "Invalid project"
                }
            )
        
        # Process file and create chunks
        process_controller = ProcessController(project_id=project_id)
        
        # Check if file exists before processing
        project_path = process_controller.project_path
        file_path = os.path.join(project_path, file_id)
        
        logger.info(f"Looking for file at: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            # List available files for debugging
            available_files = []
            if os.path.exists(project_path):
                available_files = os.listdir(project_path)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": f"File not found: {file_id}. Please upload the file first.",
                    "file_path": file_path,
                    "available_files": available_files[:10]  # Show first 10 files for debugging
                }
            )
        
        logger.info(f"File found, loading content...")
        try:
            file_content = process_controller.get_file_content(file_id=file_id)
            logger.info(f"File content loaded successfully: {len(file_content)} documents/pages")
            
            if not file_content or len(file_content) == 0:
                logger.error("File loaded but contains no content")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.PROCESS_FAILED.value,
                        "error": "File is empty or contains no extractable text. PDF may be image-based or corrupted."
                    }
                )
        except ValueError as e:
            logger.error(f"Unsupported file type or validation error: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": str(e),
                    "file_id": file_id
                }
            )
        except FileNotFoundError as e:
            logger.error(f"File not found error during loading: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": str(e),
                    "file_id": file_id,
                    "file_path": file_path
                }
            )
        except Exception as e:
            logger.error(f"Error loading file content: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": f"Error loading PDF file: {str(e)}. This might be due to a corrupted PDF, missing dependencies, or unsupported PDF format.",
                    "file_id": file_id,
                    "error_type": type(e).__name__
                }
            )
        
        logger.info(f"Creating chunks from {len(file_content)} documents...")
        try:
            chunks = process_controller.process_file_content(
                file_content=file_content,
                file_id=file_id,
                chunk_size=process_request.chunk_size or 1000,
                overlap_size=process_request.overlap_size or 200
            )
            logger.info(f"Created {len(chunks) if chunks else 0} chunks")
        except Exception as e:
            logger.error(f"Error creating chunks: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": f"Error creating chunks: {str(e)}",
                    "error_type": type(e).__name__
                }
            )
        
        if not chunks or len(chunks) == 0:
            logger.error("No chunks created from file content")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal" : ResponseSignal.PROCESS_FAILED.value,
                    "error": "No chunks created from file content. File may be empty, unreadable, or contain only images.",
                    "file_content_length": len(file_content) if file_content else 0
                }
            )
        
        # Generate embeddings for chunks
        embeddings = None
        embeddings_generated = 0
        try:
            embedding_service = EmbeddingService()
            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
            embeddings_generated = len(embeddings) if embeddings else 0
            logger.info(f"Generated {embeddings_generated} embeddings for {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            # For MVP, continue without embeddings - chunks will still be saved
            embeddings = None
        
        # Save chunks to MongoDB with embeddings
        chunk_model = ChunkModel(db_client=request.app.db_client)
        saved_count = await chunk_model.save_chunks(
            chunks=chunks,
            project_id=project._id,
            file_id=file_id,
            embeddings=embeddings
        )
        
        # Store embeddings in ChromaDB
        chromadb_stored = False
        chromadb_count = 0
        if embeddings and len(embeddings) > 0:
            try:
                vector_db_service = VectorDBService()
                chromadb_count = vector_db_service.add_chunks(
                    project_id=project_id,
                    chunks=chunks,
                    embeddings=embeddings,
                    file_id=file_id
                )
                chromadb_stored = chromadb_count > 0
                logger.info(f"Stored {chromadb_count} chunks in ChromaDB for project {project_id}")
            except Exception as e:
                logger.error(f"Error storing chunks in ChromaDB: {e}", exc_info=True)
                # Don't fail the request if ChromaDB fails - MongoDB is the source of truth
                chromadb_stored = False
                chromadb_count = 0
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.PROCESS_SUCCESS.value,
                "chunks_count": len(chunks),
                "saved_count": saved_count,
                "embeddings_generated": embeddings_generated,
                "chromadb_stored": chromadb_stored,
                "chromadb_count": chromadb_count
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}", exc_info=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Full traceback: {error_trace}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.PROCESS_FAILED.value,
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__,
                "file_id": process_request.file_id if hasattr(process_request, 'file_id') else 'unknown'
            }
        )


@data_router.post("/search/{project_id}")
async def search_endpoint(request: Request, project_id: str, search_request: SearchRequest):
    """
    Search for similar chunks using vector similarity search.
    """
    try:
        logger.info(f"=== SEARCH REQUEST RECEIVED ===")
        logger.info(f"Project ID: '{project_id}'")
        logger.info(f"Query: '{search_request.query}'")
        logger.info(f"Top K: {search_request.top_k}")
        logger.info(f"File ID filter: {search_request.file_id}")
        
        if not search_request.query or not search_request.query.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "Query cannot be empty"
                }
            )
        
        # Get project to verify it exists
        project_model = ProjectModel(db_client=request.app.db_client)
        project = await project_model.get_project_or_create_one(project_id=project_id)
        
        if not project._id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "Invalid project"
                }
            )
        
        # Generate embedding for query
        try:
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate_embedding(search_request.query.strip())
            logger.info(f"Generated query embedding: {len(query_embedding)} dimensions")
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": f"Error generating query embedding: {str(e)}"
                }
            )
        
        # Search ChromaDB for similar chunks
        try:
            vector_db_service = VectorDBService()
            top_k = search_request.top_k or 5
            
            results = vector_db_service.search_similar(
                project_id=project_id,
                query_embedding=query_embedding,
                top_k=top_k,
                file_id=search_request.file_id
            )
            
            logger.info(f"Found {len(results)} similar chunks")
            
            # Format results for response
            formatted_results = []
            for result in results:
                formatted_result = {
                    "chunk_text": result.get("chunk_text", ""),
                    "file_id": result.get("metadata", {}).get("file_id", ""),
                    "chunk_order": result.get("metadata", {}).get("chunk_order", 0),
                    "distance": result.get("distance"),
                    "metadata": result.get("metadata", {})
                }
                formatted_results.append(formatted_result)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "signal": ResponseSignal.PROCESS_SUCCESS.value,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "query": search_request.query
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": f"Error searching vector database: {str(e)}"
                }
            )
            
    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.PROCESS_FAILED.value,
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__
            }
        )


@data_router.post("/chat/{project_id}")
async def chat_endpoint(request: Request, project_id: str, chat_request: ChatRequest):
    """
    Chat endpoint for RAG queries. Generates AI responses based on document context.
    """
    try:
        logger.info(f"=== CHAT REQUEST RECEIVED ===")
        logger.info(f"Project ID: '{project_id}'")
        logger.info(f"Query: '{chat_request.query}'")
        logger.info(f"File ID filter: {chat_request.file_id}")
        logger.info(f"Top K: {chat_request.top_k}")
        
        if not chat_request.query or not chat_request.query.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "Query cannot be empty"
                }
            )
        
        # Get project to verify it exists
        project_model = ProjectModel(db_client=request.app.db_client)
        project = await project_model.get_project_or_create_one(project_id=project_id)
        
        if not project._id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": "Invalid project"
                }
            )
        
        # Generate answer using RAG service
        try:
            rag_service = RAGService()
            result = rag_service.generate_answer(
                project_id=project_id,
                query=chat_request.query.strip(),
                file_id=chat_request.file_id,
                top_k=chat_request.top_k
            )
            
            # Check if LLM generation failed (graceful degradation)
            if result.get("error"):
                logger.warning(f"RAG pipeline completed with error: {result.get('error')}")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "signal": ResponseSignal.PROCESS_SUCCESS.value,
                        "answer": None,
                        "search_results": result.get("search_results", []),
                        "sources": result.get("sources", []),
                        "query": result.get("query"),
                        "chunks_retrieved": result.get("chunks_retrieved", 0),
                        "warning": "LLM generation failed, returning search results only"
                    }
                )
            
            logger.info(f"RAG pipeline completed: {result.get('chunks_retrieved', 0)} chunks, answer generated")
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "signal": ResponseSignal.PROCESS_SUCCESS.value,
                    "answer": result.get("answer"),
                    "sources": result.get("sources", []),
                    "query": result.get("query"),
                    "chunks_retrieved": result.get("chunks_retrieved", 0)
                }
            )
            
        except ValueError as e:
            logger.error(f"Validation error in RAG service: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESS_FAILED.value,
                    "error": str(e)
                }
            )
        except RuntimeError as e:
            error_msg = str(e)
            logger.error(f"RAG service error: {error_msg}", exc_info=True)
            
            # Check for specific error types
            if "API key" in error_msg or "invalid" in error_msg.lower():
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "signal": ResponseSignal.PROCESS_FAILED.value,
                        "error": "OpenAI API configuration error. Please check your API key.",
                        "details": error_msg
                    }
                )
            elif "rate limit" in error_msg.lower():
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "signal": ResponseSignal.PROCESS_FAILED.value,
                        "error": "OpenAI API rate limit exceeded. Please try again later."
                    }
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "signal": ResponseSignal.PROCESS_FAILED.value,
                        "error": f"RAG service error: {error_msg}"
                    }
                )
            
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.PROCESS_FAILED.value,
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__
            }
        )
# upload data 

from fastapi import FastAPI , APIRouter , UploadFile , Depends , status , Request
from fastapi.responses import JSONResponse
from helpers import get_settings , Settings 
from controllers import ProjectController , ProcessController , DataController
import os 
import aiofiles
from models import ResponseSignal
import logging
from .schemes import ProcessRequest
from models.ProjectModel import ProjectModel


logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(prefix="/api/v1/data" , 
                        tags= ["api " , "router"])
@data_router.post("/upload/{project_id}")
async def upload_data(request:Request,project_id:str ,file:UploadFile,
                      app_settings:Settings =Depends(get_settings)):
    project_model = ProjectModel(
         db_client=request.app.db_client
    )
    project = await project_model.get_project_or_create_one(project_id=project_id)
    # validate the file properties ;
    is_valid , result_signal = DataController().validate_uploaded_file(file=file )
    if not is_valid :
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST 
              ,
              content={
                  "signal" : ResponseSignal.fialed_file_upload.value
              }

        )
    try:

    
        clean_file_path , file_id= DataController().generate_unique_file_path(orig_file_name=file.filename or "unknown" , project_id=project_id)
        async with aiofiles.open(clean_file_path , "wb") as f:
            while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                await f.write(chunk)
       
    except Exception as e:
            
            logger.error(f"error while uploading file : {e}")
            return JSONResponse(
                 status_code=status.HTTP_400_BAD_REQUEST , 
                content={
                    "signal" : ResponseSignal.fialed_file_upload.value
                }

            )
     
    return JSONResponse(
        
                content={
                    "signal" : ResponseSignal.success_file_upload.value  , 
                    "file_id": file_id,
                    "project_id": str(project._id) if project._id else project_id
                }

            )




@data_router.post("/process/{project_id}")
async def process_endpoint(project_id : str , process_request :ProcessRequest ):
    try:
        file_id = process_request.file_id
        process_controller = ProcessController(project_id=project_id)
        file_content = process_controller.get_file_content(file_id=file_id)
        chunks = process_controller.process_file_content(file_content=file_content , file_id=file_id)
        if not chunks or len(chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal" : ResponseSignal.PROCESS_FAILED.value
                }
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.PROCESS_SUCCESS.value,
                "chunks_count": len(chunks)
            }
        )
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.PROCESS_FAILED.value,
                "error": str(e)
            }
        )
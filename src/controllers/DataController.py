
from .BaseController import BaseController
from fastapi import UploadFile
from helpers import get_settings , Settings
from models import ResponseSignal
from .ProjectController import ProjectController
import re
import os

class DataController(BaseController):
    def __init__(self):
        super().__init__()
    
    async def validate_uploaded_file(self, file: UploadFile):
        """
        Validate uploaded file (type and size).
        Reads file content to check size, returns content for reuse.
        
        Returns:
            tuple: (is_valid: bool, result_signal: str, file_content: bytes or None)
        """
        # Check file type
        if file.content_type not in self.app_settings.FILE_ALLOWED_EXTENSIONS:
            return False, ResponseSignal.file_type_not_supported.value, None
        
        # Read file content to check size
        try:
            file_content = await file.read()
            file_size = len(file_content)
            
            # Check file size
            if file_size > self.app_settings.FILE_MAX_SIZE:
                return False, ResponseSignal.file_size_exceeded.value, None
            
            # File is valid, return content for saving
            return True, ResponseSignal.success_file_upload.value, file_content
            
        except Exception as e:
            # If reading fails, reject the file
            return False, ResponseSignal.failed_file_upload.value, None
    
    def generate_unique_file_path(self, orig_file_name: str, project_id: str):
        random_filename = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)
        clean_file_name = self.get_clean_file_name(orig_file_name=orig_file_name)
        new_file_path = os.path.join(project_path, random_filename + "_" + clean_file_name)

        while os.path.exists(new_file_path):
            random_filename = self.generate_random_string()
            new_file_path = os.path.join(project_path, random_filename + "_" + clean_file_name)

        return new_file_path , random_filename + "_" + clean_file_name


    def get_clean_file_name(self, orig_file_name: str):

        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")
        
        return cleaned_file_name

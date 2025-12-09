from enum import Enum

class ResponseSignal(Enum):
    file_type_not_supported = "File type not supported."
    file_size_exceeded = "File size exceeded the maximum limit."
    success_file_upload = "File uploaded successfully."
    failed_file_upload = "File upload failed."
    FILE_VALIDATED_SUCCESSFULLY = "FILE_VALIDATED_SUCCESSFULLY"
    PROCESS_FAILED = "process failed"
    PROCESS_SUCCESS = "process success"
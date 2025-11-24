from enum import Enum

class ResponseSignal(Enum):
    file_type_not_supported = "File type not supported."
    file_size_exceeded = "File size exceeded the maximum limit."
    success_file_upload = "File uploaded successfully."
    fialed_file_upload = "fialed_file_upload "
    FILE_VALIDATED_SUCCESSFULLY = "FILE_VALIDATED_SUCCESSFULLY"
    PROCESS_FAILED = "process failed"
    PROCESS_SUCCESS = "process success"
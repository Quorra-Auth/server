from pydantic import BaseModel

class GenericResponse(BaseModel):
    status: str

# TODO: Implement and actually use - don't know how yet
# the FastAPI SQL guide will likely have an answer
class SuccessResponse(GenericResponse):
    status: str = "success"
    data: dict

class ErrorResponse(GenericResponse):
    status: str = "error"
    detail: str


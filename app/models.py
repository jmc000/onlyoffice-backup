from pydantic import BaseModel


# ONLYOFFICE UPLOADER
class UploadNestedResponse(BaseModel):
    title: str
    version: int

class UploadReturnedResponse(BaseModel):
    response: list[UploadNestedResponse]
    status: int
    statusCode: int

# GET MY DOCUMENTS FOLDER ID
class Current(BaseModel):
    id: int

class GetMyDocumentsFolderIdNestedResponse(BaseModel):
    current: Current

class GetMyDocumentsFolderIdReturnedResponse(BaseModel):
    response: GetMyDocumentsFolderIdNestedResponse
    status: int
    statusCode: int

# CREATE UPLOAD SESSION
class CreateUploadSessionData(BaseModel):
    location: str

class CreateUploadSessionNestedResponse(BaseModel):
    data: CreateUploadSessionData

class CreateUploadSessionReturnedResponse(BaseModel):
    response: CreateUploadSessionNestedResponse
    status: int
    statusCode: int

# UPLOAD CHUNK
class UploadChunkFile(BaseModel):
    version: int

class UploadChunkReturnedResponseData(BaseModel):
    file: UploadChunkFile | None = None
    message: str | None = None
    uploaded: bool | None = None
    location: str | None = None

class UploadChunkReturnedResponse(BaseModel):
    success: bool
    data: UploadChunkReturnedResponseData

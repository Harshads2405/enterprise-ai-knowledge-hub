from pydantic import BaseModel


class Citation(BaseModel):
    document_id: int
    chunk_id: int
    chunk_index: int
    source_name: str
    distance: float
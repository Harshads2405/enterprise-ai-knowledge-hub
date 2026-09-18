from typing import List

from pydantic import BaseModel, Field


class MultiQueryResponse(BaseModel):
    queries: List[str] = Field(
        default_factory=list,
        min_length=1,
        max_length=3,
    )
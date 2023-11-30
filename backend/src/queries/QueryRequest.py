from pydantic import BaseModel, StrictFloat, PositiveInt
from typing import Dict, List, Tuple
from datetime import datetime


class STACCollectionRequest(BaseModel):
    query: str
    keywords: list[str]
    limit: PositiveInt

class WebRequest(BaseModel):
    query: str
    limit: PositiveInt

class PubRequest(BaseModel):
    query: str
    keywords: list[str]
    limit: PositiveInt

class STACItemRequest(BaseModel):
    collection_id: str
    limit: PositiveInt
    location_filters: List[object] | None = None
    time_interval: List[object]

class GeoparseRequest(BaseModel):
    query: str
    
class QueryAnalyzerRequest(BaseModel):
    query :str

class NotebookExportRequest(BaseModel):
    collection_id: str
    location_filters: List[object] | None = None
    time_interval: List[object]

from pydantic import BaseModel, StrictFloat, PositiveInt
from typing import Dict, List, Tuple
from datetime import datetime


class STACCollectionRequest(BaseModel):
    query: str
    keywords: list[str]
    limit: PositiveInt
    location_filter: object | None = None

class WebRequest(BaseModel):
    query: str
    limit: PositiveInt
    location_filter: object | None = None

class PubRequest(BaseModel):
    query: str
    keywords: list[str]
    limit: PositiveInt

class STACItemRequest(BaseModel):
    collection_id: str
    limit: PositiveInt
    location_filter: object | None = None
    time_interval: List[object]

class QueryAnalyzerRequest(BaseModel):
    query :str

class NotebookExportRequest(BaseModel):
    collection_id: str
    location_filter: object | None = None
    time_interval: List[object]

class GeotweetRequest(BaseModel):
    only_floods: bool
    limit: PositiveInt


class GraphQueryRequest(BaseModel):
    keywords: list[dict]
    authors: list[dict]
    eo_nodes: list[dict]


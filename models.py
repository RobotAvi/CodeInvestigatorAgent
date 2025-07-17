from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


class C4Level(str, Enum):
    CONTEXT = "context"
    CONTAINER = "container"
    COMPONENT = "component"
    CODE = "code"


class Message(BaseModel):
    id: str
    agent_id: str
    content: str
    role: str  # user, assistant, system
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class Agent(BaseModel):
    id: str
    name: str
    status: AgentStatus
    created_at: datetime
    last_activity: datetime
    context: Dict[str, Any]
    repositories: List[str]
    c4_diagrams: Dict[str, Any]


class C4Element(BaseModel):
    id: str
    name: str
    type: str
    level: C4Level
    description: str
    technology: Optional[str] = None
    relationships: List[str] = []
    properties: Dict[str, Any] = {}
    parent_id: Optional[str] = None
    children: List[str] = []


class C4Diagram(BaseModel):
    id: str
    name: str
    level: C4Level
    elements: List[C4Element]
    relationships: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class Repository(BaseModel):
    id: str
    name: str
    url: str
    branch: str
    language: str
    services: List[str]
    components: List[str]
    last_analyzed: datetime


class AnalysisResult(BaseModel):
    agent_id: str
    repository_id: str
    analysis_type: str
    result: Dict[str, Any]
    timestamp: datetime
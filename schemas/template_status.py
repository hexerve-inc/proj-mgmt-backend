from typing import Optional
from pydantic import BaseModel, ConfigDict
from models.workflow_status import WorkflowGroup

class TemplateStatusResponse(BaseModel):
    id: str
    template_id: str
    name: str
    group_key: WorkflowGroup
    color: Optional[str] = None
    position: int
    is_default: bool

    model_config = ConfigDict(from_attributes=True)

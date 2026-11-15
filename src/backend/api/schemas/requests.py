"""API request schemas."""
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=1000, description="Research query or topic")
    scope: str = Field(default="comprehensive", description="Research depth and scope")
    max_iterations: int = Field(default=2, ge=1, le=5, description="Maximum refinement loops")

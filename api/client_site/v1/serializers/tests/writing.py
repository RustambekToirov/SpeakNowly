from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class WritingPart1Serializer(BaseModel):
    """Serializer for part 1 of a writing test."""
    content: str = Field(..., description="Task content")
    answer: Optional[str] = Field(None, description="User's answer")
    diagram: Optional[str] = Field(None, description="Diagram image path")
    diagram_data: Optional[Dict[str, Any]] = Field(None, description="Diagram data")

    @classmethod
    async def from_orm(cls, obj) -> "WritingPart1Serializer":
        diagram_url = None
        if obj.diagram:
            diagram_url = f"/media/{obj.diagram.lstrip('/')}"
        return cls(
            content=obj.content,
            answer=obj.answer,
            diagram=diagram_url,
            diagram_data=obj.diagram_data,
        )


class WritingPart2Serializer(BaseModel):
    """Serializer for part 2 of a writing test."""
    content: str = Field(..., description="Task content")
    answer: Optional[str] = Field(None, description="User's answer")

    @classmethod
    async def from_orm(cls, obj) -> "WritingPart2Serializer":
        return cls(
            content=obj.content,
            answer=obj.answer,
        )


class WritingSerializer(BaseModel):
    """Serializer for a writing test with its parts."""
    id: int = Field(..., description="ID of the writing test")
    start_time: datetime = Field(..., description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    status: str = Field(..., description="Status")
    part1: Optional[WritingPart1Serializer] = Field(None, description="Part 1")
    part2: Optional[WritingPart2Serializer] = Field(None, description="Part 2")

    @classmethod
    async def from_orm(cls, obj) -> "WritingSerializer":
        part1_obj = await obj.part1
        part2_obj = await obj.part2
        part1 = await WritingPart1Serializer.from_orm(part1_obj) if part1_obj else None
        part2 = await WritingPart2Serializer.from_orm(part2_obj) if part2_obj else None
        return cls(
            id=obj.id,
            start_time=obj.start_time,
            end_time=obj.end_time,
            status=obj.status,
            part1=part1,
            part2=part2,
        )


class WritingSubmitRequest(BaseModel):
    part1_answer: Optional[str] = Field(None, description="Answer for part 1")
    part2_answer: Optional[str] = Field(None, description="Answer for part 2")
from pydantic import BaseModel, Field

class BookQuery(BaseModel):
    title: str = Field(..., description="The title of the book the user is referring to.")
    author: str | None = Field(None, description="The author if known or inferable.")
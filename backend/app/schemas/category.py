from pydantic import BaseModel
from typing import List, Optional

class CategoryTreeItem(BaseModel):
    value: int
    label: str
    children: Optional[List["CategoryTreeItem"]] = None

CategoryTreeItem.model_rebuild()
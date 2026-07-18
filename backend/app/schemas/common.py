from typing import Optional, Any
from pydantic import BaseModel

#固定套路
class ResponseModel(BaseModel):
    code: str = "200"
    message: str = "success"
    data: Optional[Any] = None
from pydantic import BaseModel


class NetworkResponse(BaseModel):
    network: str
    block_height: int
    is_syncing: bool

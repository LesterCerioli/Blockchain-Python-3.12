from pydantic import BaseModel


class NetworkResponse(BaseModel):
    chain_id: int
    network_name: str
    is_syncing: bool

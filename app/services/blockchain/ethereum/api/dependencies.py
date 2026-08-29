from fastapi import Request

from ..domain.interfaces.health_monitor import IHealthMonitor
from ..domain.interfaces.network_service import INetworkService


def get_health_service(request: Request) -> IHealthMonitor:
    return request.app.state.health_service


def get_network_service(request: Request) -> INetworkService:
    return request.app.state.network_service

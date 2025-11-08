from fastapi import Request
from src.modules.core import Logger


def get_logger(request: Request) -> Logger:
    return request.app.state.logger

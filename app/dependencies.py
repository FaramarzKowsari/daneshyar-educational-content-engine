from __future__ import annotations

from fastapi import Request


def get_db(request: Request):
    yield from request.app.state.database.get_session()


def get_services(request: Request):
    return request.app.state.services

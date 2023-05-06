import asyncio

import fastapi
from fastapi import FastAPI, Request
from pydantic import BaseModel

import servers
from tg_app import TGAppController


class ImaliveRequest(BaseModel):
    token: str


class ImaliveResponse(BaseModel):
    message: str
    code: int


def create_app(tg_app: TGAppController, secret_key: str) -> fastapi.FastAPI:
    app = FastAPI()

    @app.post("/imalive")
    async def imalive(body: ImaliveRequest, request: Request) -> ImaliveResponse:
        if body.token != secret_key:
            return ImaliveResponse(message="invalid token", code=403)

        is_new = servers.set_active_now(request.client.host)
        if is_new:
            asyncio.create_task(tg_app.notify_users_on_new_server(request.client.host))

        return ImaliveResponse(message="ok", code=200)

    return app

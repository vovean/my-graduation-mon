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


def create_app(tg_app: TGAppController, secret_key: str, sm: servers.Manager) -> fastapi.FastAPI:
    app = FastAPI()

    @app.post("/imalive")
    async def imalive(body: ImaliveRequest, request: Request) -> ImaliveResponse:
        if body.token != secret_key:
            return ImaliveResponse(message="invalid token", code=403)

        server_state = sm.set_server_active(request.client.host)
        if server_state == servers.SERVER_NEW:
            asyncio.create_task(tg_app.notify_users_on_new_server(request.client.host))
        elif server_state == servers.SERVER_ACTIVE_AGAIN:
            asyncio.create_task(tg_app.notify_users_server_active_again(request.client.host))

        return ImaliveResponse(message="ok", code=200)

    return app

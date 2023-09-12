import uvicorn
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

import settings
import views

app = FastAPI()
app.include_router(views.router)
app.add_middleware(BaseHTTPMiddleware, dispatch=views.get_session)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.settings.env == "local" else False,
    )

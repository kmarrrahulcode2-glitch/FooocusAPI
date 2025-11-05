"""
Entry for startup fastapi server
"""
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse

import uvicorn

from apis.routes.generate import secure_router as generate
from apis.routes.query import secure_router as query
from apis.routes.query import router
from apis.utils import file_utils
from apis.utils import api_utils

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow access from all sources
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all request headers
)


app.include_router(query)
app.include_router(generate)
app.include_router(router)


@app.get("/", tags=["Query"])
async def root():
    """
    Root endpoint
    :return: root endpoint
    """
    return RedirectResponse("/docs")


def run_server(arguments):
    """
    Run the FastAPI server
    :param arguments: command line arguments
    """
    if arguments.apikey != "":
        api_utils.APIKEY_AUTH = arguments.apikey

    os.environ["WEBHOOK_URL"] = arguments.webhook_url
    try:
        api_port = int(os.environ['API_PORT'])
    except KeyError:
        try:
            api_port = int(arguments.port) + 1
        except TypeError:
            api_port = int(os.environ["GRADIO_SERVER_PORT"]) + 1

    # Parse the base_url to handle cases where it includes a scheme
    parsed_url = urlparse(arguments.base_url)

    if parsed_url.scheme:
        # If a scheme is provided, use the full URL
        file_utils.STATIC_SERVER_BASE = f"{arguments.base_url}"
    else:
        file_utils.STATIC_SERVER_BASE = f"http://{arguments.base_url}:{api_port}"

    # If the user requested no web UI but bound to all interfaces, optionally expose the API
    # via an ngrok tunnel (if pyngrok is installed). This provides a temporary public URL
    # for the API and updates STATIC_SERVER_BASE accordingly.
    try:
        if getattr(arguments, 'listen', None) == '0.0.0.0':
            try:
                from pyngrok import ngrok
                # Respect NGROK_AUTHTOKEN env var if set; pyngrok will pick it up automatically
                public_tunnel = ngrok.connect(addr=api_port, proto="http", bind_tls=True)
                public_url = public_tunnel.public_url
                print(f"[ngrok] Public API URL: {public_url}")
                file_utils.STATIC_SERVER_BASE = public_url
            except Exception as e:
                print(f"[ngrok] Failed to start ngrok tunnel: {e}")
    except Exception:
        pass
    uvicorn.run(app, host=arguments.listen, port=api_port)

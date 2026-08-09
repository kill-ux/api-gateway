import os
import logging
from dotenv import load_dotenv
from waitress import serve
from paste.translogger import TransLogger
from app import create_app, get_env_variable

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = create_app()

APIGATEWAY_PORT = get_env_variable("APIGATEWAY_PORT")

if __name__ == "__main__":
    logged_app = TransLogger(app, setup_console_handler=True)

    logging.info(f"Starting Waitress server on 0.0.0.0:{APIGATEWAY_PORT}")
    
    serve(
        logged_app,
        host="0.0.0.0",
        port=int(APIGATEWAY_PORT),
        threads=8
    )
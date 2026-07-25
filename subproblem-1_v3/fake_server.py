"""
fake_server.py

A lightweight fake Spring Boot server for testing the
Synthetic Cybersecurity Log Generator.

Endpoint

POST /api/v1/logs/ingest

Runs on

http://localhost:8080

Author:
    Sagar Kumar Sahu
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

HOST = "localhost"
PORT = 8080

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)

logger = logging.getLogger(__name__)


class FakeSpringBootHandler(BaseHTTPRequestHandler):
    """
    Fake REST endpoint.
    """

    def do_POST(self):
        """
        Handle POST requests.
        """

        if self.path != "/api/v1/logs/ingest":

            self.send_response(404)

            self.end_headers()

            return

        try:

            content_length = int(

                self.headers["Content-Length"]

            )

            body = self.rfile.read(

                content_length

            )

            payload = json.loads(

                body.decode("utf-8")

            )

            logger.info("=" * 70)

            logger.info(

                "Received log"

            )

            logger.info(

                json.dumps(

                    payload,

                    indent=4

                )

            )

            logger.info("=" * 70)

            self.send_response(200)

            self.send_header(

                "Content-Type",

                "application/json"

            )

            self.end_headers()

            response = {

                "status": "success",

                "message": "Log received"

            }

            self.wfile.write(

                json.dumps(response).encode()

            )

        except Exception as ex:

            logger.exception(ex)

            self.send_response(500)

            self.end_headers()

    def log_message(self, format, *args):
        """
        Disable default HTTP logging.
        """

        return


def main():

    server = HTTPServer(

        (HOST, PORT),

        FakeSpringBootHandler

    )

    logger.info("")

    logger.info("=" * 70)

    logger.info("Fake Spring Boot Server Started")

    logger.info(

        "Listening on : http://localhost:8080"

    )

    logger.info(

        "Endpoint     : /api/v1/logs/ingest"

    )

    logger.info("=" * 70)

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        logger.info("Stopping server...")

        server.server_close()


if __name__ == "__main__":

    main()
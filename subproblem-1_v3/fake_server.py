from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# Bind to 0.0.0.0 for Docker container exposure
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8001))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


class FakeSpringBootHandler(BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        """Adds CORS headers to allow browser requests from React on localhost:3000"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handles browser preflight CORS checks"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        # Allow both generator attack injection and log ingestion paths
        if self.path not in [
            "/api/v1/generator/inject-attack",
            "/api/v1/logs/ingest",
        ]:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""
            payload = json.loads(body.decode("utf-8")) if body else {}

            logger.info("=" * 70)
            logger.info(f"Received Request on {self.path}")
            logger.info(json.dumps(payload, indent=4))
            logger.info("=" * 70)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()

            response = {
                "status": "success",
                "message": f"Processed request for path {self.path}",
                "data": payload,
            }

            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as ex:
            logger.exception(ex)
            self.send_response(500)
            self._set_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        return


def main():
    server = HTTPServer((HOST, PORT), FakeSpringBootHandler)

    logger.info("")
    logger.info("=" * 70)
    logger.info("Generator Control Server Started")
    logger.info(f"Listening on : http://0.0.0.0:{PORT}")
    logger.info("Endpoints    : /api/v1/generator/inject-attack")
    logger.info("               /api/v1/logs/ingest")
    logger.info("=" * 70)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.server_close()


if __name__ == "__main__":
    main()


from __future__ import annotations

import json
import logging
import time
from typing import Dict

import requests
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    RequestException,
    Timeout,
)

from config import Config

logger = logging.getLogger(__name__)


class NetworkDispatcher:


    def __init__(
        self,
        endpoint: str | None = None
    ) -> None:

        self.endpoint = endpoint or Config.API_URL

        self.timeout = Config.REQUEST_TIMEOUT

        self.max_retries = Config.MAX_RETRIES

        self.initial_backoff = Config.INITIAL_BACKOFF



    def send_log(
        self,
        log_payload: Dict
    ) -> bool:


        delay = self.initial_backoff

        for attempt in range(
            1,
            self.max_retries + 1
        ):

            try:

                response = requests.post(

                    url=self.endpoint,

                    headers={

                        "Content-Type": "application/json",

                        "X-API-Key": Config.API_KEY

                    },

                    data=json.dumps(log_payload),

                    timeout=self.timeout

                )

                response.raise_for_status()

                logger.info(

                    "Successfully sent log for %s",

                    log_payload["entity_id"]

                )

                return True

            except ConnectionError as ex:

                logger.warning(

                    "Connection failed "
                    "(Attempt %d/%d): %s",

                    attempt,

                    self.max_retries,

                    ex

                )

            except Timeout as ex:

                logger.warning(

                    "Timeout "
                    "(Attempt %d/%d): %s",

                    attempt,

                    self.max_retries,

                    ex

                )

            except HTTPError as ex:

                logger.error(

                    "HTTP Error "
                    "(Attempt %d/%d): %s",

                    attempt,

                    self.max_retries,

                    ex

                )

            except RequestException as ex:

                logger.error(

                    "Unexpected request error: %s",

                    ex

                )

            except Exception as ex:

                logger.exception(

                    "Unexpected dispatcher error: %s",

                    ex

                )

            logger.info(

                "Retrying in %.1f seconds...",

                delay

            )

            time.sleep(delay)

            delay *= 2

        logger.error(

            "Failed to send log after %d retries.",

            self.max_retries

        )

        return False



    def send_batch(
        self,
        logs: list[Dict]
    ) -> int:


        success = 0

        for log in logs:

            if self.send_log(log):

                success += 1

        logger.info(

            "Batch complete: %d/%d delivered.",

            success,

            len(logs)

        )

        return success
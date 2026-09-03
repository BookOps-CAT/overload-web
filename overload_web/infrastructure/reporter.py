"""Adapter module that defines a handlers used to create and write processing reports.

Classes:

`GoogleSheetsReporter`
    Concrete implementation of `ReportWriter` protocol which uses google API client to
    write processing reports to a Google Sheet.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore

logger = logging.getLogger(__name__)


class GoogleSheetsReporter:
    def configure_sheet(self) -> Credentials:
        """
        Get or update credentials for google sheets API and save token to file.

        Args:
            None

        Returns:
            google.oauth2.credentials.Credentials: Credentials object for
            google sheet API.
        """
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        token_uri = "https://oauth2.googleapis.com/token"

        creds_dict = {
            "token": os.getenv("GOOGLE_SHEET_TOKEN"),
            "refresh_token": os.getenv("GOOGLE_SHEET_REFRESH_TOKEN"),
            "token_uri": token_uri,
            "client_id": os.getenv("GOOGLE_SHEET_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_SHEET_CLIENT_SECRET"),
            "scopes": scopes,
            "universe_domain": "googleapis.com",
            "account": "",
            "expiry": "2026-01-01T01:00:00.000000Z",
        }
        flow_dict = {
            "installed": {
                "client_id": os.getenv("GOOGLE_SHEET_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_SHEET_CLIENT_SECRET"),
                "project_id": "marc-record-validator",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": token_uri,
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"],
            }
        }

        try:
            creds = Credentials.from_authorized_user_info(creds_dict)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif not creds or not creds.valid:
                logger.debug("API token not found. Running credential config flow.")
                flow = InstalledAppFlow.from_client_config(flow_dict, scopes)
                creds = flow.run_local_server()
            return creds
        except (ValueError, RefreshError) as e:
            raise e

    def prep_report(self, data: list[dict[str, Any]]) -> list[list[str]]:
        """
        Prep output for google sheet.

        Args:
            data: dictionary containing report data to be written.

        Returns:
            The data to be written as a list of lists
        """
        if not data:
            return []
        headers = list(data[0])
        return [
            ["" if row.get(header) is None else str(row[header]) for header in headers]
            for row in data
        ]

    def write_report(self, data: list[list[str]]) -> None:
        """
        Write output to google sheet.

        Args:
            data: dictionary containing report data to be written.

        Returns:
            None
        """
        creds = self.configure_sheet()
        sheet_name = os.environ["GOOGLE_SHEET_NAME"]
        body = {
            "majorDimension": "ROWS",
            "range": f"{sheet_name}!A1:O10000",
            "values": data,
        }
        try:
            service = build("sheets", "v4", credentials=creds, cache_discovery=False)
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=os.environ["GOOGLE_SHEET_ID"],
                    range=f"{sheet_name}!A1:O10000",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                    includeValuesInResponse=True,
                )
                .execute()
            )
            logger.info(f"Data written to Google Sheet: {result}")
            return
        except (ValueError, RefreshError) as e:
            logger.error(f"Unable to configure google sheet API credentials: {e}")
        except (HttpError, TimeoutError) as e:
            logger.error(f"Unable to send data to google sheet: {e}")
        logger.error("Data not written to sheet.")

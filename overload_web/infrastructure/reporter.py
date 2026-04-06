from __future__ import annotations

import logging
import os
from collections import defaultdict
from typing import Any

import pandas as pd
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore

logger = logging.getLogger(__name__)


class PandasReportHandler:
    def create_call_number_report(
        self, report_data: dict[str, list[Any]], record_type: str
    ) -> dict[str, list[Any]] | None:
        df = pd.DataFrame(data=report_data)
        match_df = df[~df["call_number_match"]]
        if record_type == "cat":
            missing_df = df[df["call_number"].isnull() & df["target_call_no"].isnull()]
            match_df = pd.concat([match_df, missing_df])
        if match_df.empty:
            return None
        df_dict = match_df.to_dict("list")
        return {str(k): v for k, v in df_dict.items()}

    def create_detailed_report(
        self, report_data: dict[str, list[Any]]
    ) -> dict[str, list[Any]] | None:
        df = pd.DataFrame(data=report_data)
        df_dict = df.to_dict("list")
        return {str(k): v for k, v in df_dict.items()}

    def create_duplicate_report(
        self, report_data: dict[str, list[Any]]
    ) -> dict[str, list[Any]]:
        df = pd.DataFrame(data=report_data)
        filtered_df = df[
            df["duplicate_records"].notnull()
            | df["mixed"].notnull()
            | df["other"].notnull()
        ]
        df_dict = filtered_df.to_dict("list")
        return {str(k): v for k, v in df_dict.items()}

    def create_vendor_report(
        self, report_data: dict[str, list[str]]
    ) -> dict[str, list[Any]]:
        df = pd.DataFrame(data=report_data)
        vendor_data = defaultdict(list)
        for vendor, content in df.groupby("vendor"):
            attach = content[content["action"] == "attach"]["action"].count()
            insert = content[content["action"] == "insert"]["action"].count()
            update = content[content["action"] == "overlay"]["action"].count()
            vendor_data["vendor"].append(vendor)
            vendor_data["attach"].append(attach)
            vendor_data["insert"].append(insert)
            vendor_data["update"].append(update)
            vendor_data["total"].append(attach + insert + update)
        return vendor_data


class GoogleSheetsReporter:
    def __init__(self) -> None:
        self.creds = self.configure_sheet()

    def configure_sheet(self) -> Credentials:
        """
        Get or update credentials for google sheets API and save token to file.

        Args:
            None

        Returns:
            google.oauth2.credentials.Credentials: Credentials object for
            google sheet API.
        """
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/accounts.reauth",
        ]
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

    def prep_report(self, data: dict[str, list[Any]]) -> list[list[str]]:
        """
        Prep output for google sheet.

        Args:
            data: dictionary containing report data to be written.

        Returns:
            The data to be writte as a list of lists
        """
        df = pd.DataFrame(data=data, dtype="str")
        df.fillna("", inplace=True)
        return df.values.tolist()

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
            service = build("sheets", "v4", credentials=creds)
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

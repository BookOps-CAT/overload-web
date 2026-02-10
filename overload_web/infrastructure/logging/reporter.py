from __future__ import annotations

import logging
import os
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
    @staticmethod
    def report_to_html(report_data: dict[str, list[Any]]) -> str:
        df = pd.DataFrame(data=report_data)
        return df.to_html()


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

    def create_duplicate_report(self, data: dict[str, Any]) -> list[list[Any]]:
        if data["collection"][0] == "BL":
            other = "research"
            dups = "branch duplicates"
        else:
            other = "branches"
            dups = "research duplicates"
        df_data = {
            "vendor": data["vendor"],
            "resource_id": data["resource_id"],
            "target_bib_id": data["target_bib_id"],
            dups: data["duplicate_records"],
            "mixed": data["mixed"],
            other: data["other"],
        }
        df = pd.DataFrame(data=df_data)
        filtered_df = df[
            df[dups].notnull() | df["mixed"].notnull() | df["other"].notnull()
        ]
        df_out = filtered_df.assign(
            date=data["date"], corrected="no", agency=data["record_type"]
        )
        columns = [
            "date",
            "agency",
            "vendor",
            "vendor_id",
            "target_id",
            "duplicate bibs",
            "corrected",
        ]
        df_out = df_out[columns]

        if data["library"][0] == "NYPL":
            mask = (df_out.iloc[:, 5].isnull() & df_out.iloc[:, 6].isnull()) & ~(
                df_out.iloc[:, 7].notnull() & df_out.iloc[:, 7].str.contains(",")
            )
            df_out.loc[mask, "corrected"] = "no action"
        else:
            mask = df_out.iloc[:, 5].isnull()
            df_out.loc[mask, "corrected"] = "no action"
        df_out.fillna("", inplace=True)
        return df_out.values.tolist()

    def create_call_number_report(self, data: dict[str, Any]) -> list[list[Any]]:
        if data["collection"][0] == "BL":
            dups = "branch duplicates"
        else:
            dups = "research duplicates"
        df_data = {
            "vendor": data["vendor"],
            "resource_id": data["resource_id"],
            "target_bib_id": data["target_bib_id"],
            "call_number": data["call_number"],
            "target_call_no": data["target_call_no"],
            dups: data["duplicate_records"],
            "call_number_match": data["call_number_match"],
        }
        df = pd.DataFrame(data=df_data)
        match_df = df[~df["call_no_match"]]
        if data["record_type"][0] == "cat":
            missing_df = df[df["call_number"].isnull() & df["target_call_no"].isnull()]
            match_df = pd.concat([match_df, missing_df])
        df_out = match_df.assign(date=data["date"], corrected="no")
        columns = [
            "date",
            "vendor",
            "vendor_id",
            "target_id",
            "vendor_callNo",
            "target_callNo",
            "duplicate bibs",
            "corrected",
        ]
        df_out = df_out[columns]
        df_out.fillna("", inplace=True)
        return df_out.values.tolist()

    def write_report_to_sheet(self, data: list[list[Any]]) -> None:
        """
        Write output of validation to google sheet.

        Args:
            data: dictionary containing report data to be written.

        Returns:
            None
        """
        sheet_name = os.environ["GOOGLE_SHEET_NAME"]
        body = {
            "majorDimension": "ROWS",
            "range": f"{sheet_name}!A1:O10000",
            "values": data,
        }
        creds = self.configure_sheet()
        try:
            service = build("sheets", "v4", credentials=creds)
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=os.environ["GOOGLE_SHEET_ID"],
                    range=f"{sheet_name.upper()}!A1:O10000",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                    includeValuesInResponse=True,
                )
                .execute()
            )
            logger.info(f"Data written to Google Sheet: {result}")
        except (ValueError, RefreshError) as e:
            logger.error(f"Unable to configure google sheet API credentials: {e}")
        except (HttpError, TimeoutError) as e:
            logger.error(f"Unable to send data to google sheet: {e}")
        logger.error(f"({os.getenv('GOOGLE_SHEET_NAME')}) Data not written to sheet.")

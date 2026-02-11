from __future__ import annotations

import datetime
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

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class PandasReportHandler:
    @staticmethod
    def report_to_html(report_data: dict[str, list[Any]], classes: list[str]) -> str:
        df = pd.DataFrame(data=report_data)
        return df.to_html(index=False, classes=classes, justify="unset")

    @staticmethod
    def list2dict(report_data: list[bibs.MatchAnalysis]) -> dict[str, list[Any]]:
        return {
            "action": [i.action for i in report_data],
            "call_number": [i.call_number for i in report_data],
            "call_number_match": [i.call_number_match for i in report_data],
            "collection": [i.collection for i in report_data],
            "decision": [i.decision for i in report_data],
            "duplicate_records": [i.duplicate_records for i in report_data],
            "library": [i.library for i in report_data],
            "mixed": [i.mixed for i in report_data],
            "other": [i.other for i in report_data],
            "record_type": [i.record_type for i in report_data],
            "resource_id": [i.resource_id for i in report_data],
            "target_bib_id": [i.target_bib_id for i in report_data],
            "target_call_no": [i.target_call_no for i in report_data],
            "target_title": [i.target_title for i in report_data],
            "updated_by_vendor": [i.updated_by_vendor for i in report_data],
            "vendor": [i.vendor for i in report_data],
        }

    @staticmethod
    def create_vendor_breakdown(
        report_data: dict[str, list[Any]],
    ) -> dict[str, list[Any]]:
        data = {k: v for k, v in report_data.items() if k in ["vendor", "action"]}
        df = pd.DataFrame(data=data)
        vendor_data: dict[str, list[Any]] = {
            "vendor": [],
            "attach": [],
            "insert": [],
            "update": [],
            "total": [],
        }
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

    @staticmethod
    def create_duplicate_report(
        report_data: dict[str, list[Any]],
    ) -> list[list[Any]]:
        df_data = {
            k: v
            for k, v in report_data.items()
            if k
            in [
                "vendor",
                "resource_id",
                "target_bib_id",
                "duplicate_records",
                "mixed",
                "other",
                "record_type",
            ]
        }
        df = pd.DataFrame(data=df_data)
        filtered_df = df[
            df["duplicate_records"].notnull()
            | df["mixed"].notnull()
            | df["other"].notnull()
        ]
        df_out = filtered_df.assign(date=datetime.datetime.now())
        df_out.fillna("", inplace=True)
        return df_out.values.tolist()

    @staticmethod
    def create_call_number_report(
        report_data: dict[str, list[Any]],
    ) -> list[list[Any]]:
        df_data = {
            k: v
            for k, v in report_data.items()
            if k
            in [
                "vendor",
                "resource_id",
                "target_bib_id",
                "duplicate_records",
                "call_number_match",
                "record_type",
                "call_number",
                "target_call_no",
            ]
        }
        df = pd.DataFrame(data=df_data)
        match_df = df[~df["call_number_match"]]
        if report_data["record_type"] and report_data["record_type"][0] == "cat":
            missing_df = df[df["call_number"].isnull() & df["target_call_no"].isnull()]
            match_df = pd.concat([match_df, missing_df])
        df_out = match_df.assign(date=datetime.datetime.now())
        df_out.fillna("", inplace=True)
        return df_out.values.tolist()

    @staticmethod
    def create_detailed_report(
        report_data: dict[str, list[Any]],
    ) -> dict[str, list[Any]]:
        df_data = {
            k: v
            for k, v in report_data.items()
            if k
            in [
                "vendor",
                "resource_id",
                "action",
                "target_bib_id",
                "updated",
                "call_number_match",
                "call_number",
                "target_call_no",
                "duplicates",
                "mixed",
                "other",
            ]
        }
        df = pd.DataFrame(data=df_data)
        df.fillna("", inplace=True)
        return df_data


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

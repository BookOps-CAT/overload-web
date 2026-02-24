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

from overload_web.domain.models import bibs, reports

logger = logging.getLogger(__name__)


class PandasReportHandler:
    def __init__(self, library: str, collection: str | None, record_type: str) -> None:
        self.library = library
        self.collection = collection
        self.record_type = record_type

    def create_call_number_report(
        self, report_data: dict[str, list[Any]]
    ) -> reports.CallNumberReport | None:
        df = pd.DataFrame(data=report_data)
        match_df = df[~df["call_number_match"]]
        if self.record_type == "cat":
            missing_df = df[df["call_number"].isnull() & df["target_call_no"].isnull()]
            match_df = pd.concat([match_df, missing_df])
        if match_df.empty:
            return None
        return reports.CallNumberReport(
            resource_id=match_df["resource_id"].to_list(),
            target_bib_id=match_df["target_bib_id"].to_list(),
            call_number_match=match_df["call_number_match"].to_list(),
            call_number=match_df["call_number"].to_list(),
            target_call_no=match_df["target_call_no"].to_list(),
            duplicate_records=match_df["duplicate_records"].to_list(),
            vendor=match_df["vendor"].to_list(),
        )

    def create_detailed_report(
        self, report_data: dict[str, list[Any]]
    ) -> reports.DetailedReport:
        return reports.DetailedReport(
            vendor=report_data["vendor"],
            resource_id=report_data["resource_id"],
            action=report_data["action"],
            target_bib_id=report_data["target_bib_id"],
            updated=report_data["updated_by_vendor"],
            call_number_match=report_data["call_number_match"],
            call_number=report_data["call_number"],
            target_call_no=report_data["target_call_no"],
            duplicate_records=report_data["duplicate_records"],
            mixed=report_data["mixed"],
            other=report_data["other"],
        )

    def create_duplicate_report(
        self, report_data: dict[str, list[Any]]
    ) -> reports.DuplicateReport:
        df = pd.DataFrame(data=report_data)
        filtered_df = df[
            df["duplicate_records"].notnull()
            | df["mixed"].notnull()
            | df["other"].notnull()
        ]
        return reports.DuplicateReport(
            vendor=filtered_df["vendor"].to_list(),
            resource_id=filtered_df["resource_id"].to_list(),
            target_bib_id=filtered_df["target_bib_id"].to_list(),
            duplicate_records=filtered_df["duplicate_records"].to_list(),
            mixed=filtered_df["mixed"].to_list(),
            other=filtered_df["other"].to_list(),
        )

    def create_summary_report(
        self,
        file_names: list[str],
        total_files_processed: int,
        total_records_processed: int,
        report_data: dict[str, list[Any]],
        missing_barcodes: list[str] = [],
        processing_integrity: str | None = None,
    ) -> reports.SummaryReport:
        return reports.SummaryReport(
            library=[self.library],
            collection=[self.collection],
            record_type=[self.record_type],
            file_names=[file_names],
            total_files_processed=[total_files_processed],
            total_records_processed=[total_records_processed],
            missing_barcodes=[missing_barcodes],
            processing_integrity=[processing_integrity],
            vendor_breakdown=self.create_vendor_report(report_data),
            duplicates_report=self.create_duplicate_report(report_data),
            call_number_issues=self.create_call_number_report(report_data),
        )

    def create_vendor_report(
        self, report_data: dict[str, list[Any]]
    ) -> reports.VendorReport:
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
        return reports.VendorReport(
            vendor=vendor_data["vendor"],
            attach=vendor_data["attach"],
            insert=vendor_data["insert"],
            update=vendor_data["update"],
            total=vendor_data["total"],
        )

    def list2dict(self, report_data: list[bibs.DomainBib]) -> dict[str, list[Any]]:
        vendor = [i.vendor for i in report_data]
        analysis = [i.analysis for i in report_data]
        return {
            "action": [i.action for i in analysis],
            "call_number": [i.call_number for i in analysis],
            "call_number_match": [i.call_number_match for i in analysis],
            "duplicate_records": [i.duplicate_records for i in analysis],
            "mixed": [i.mixed for i in analysis],
            "other": [i.other for i in analysis],
            "resource_id": [i.resource_id for i in analysis],
            "target_bib_id": [i.target_bib_id for i in analysis],
            "target_call_no": [i.target_call_no for i in analysis],
            "target_title": [i.target_title for i in analysis],
            "updated_by_vendor": [i.updated_by_vendor for i in analysis],
            "vendor": vendor,
        }

    def report_to_html(
        self, report_data: dict[str, list[Any]], classes: list[str]
    ) -> str:
        df = pd.DataFrame(data=report_data)
        return df.to_html(index=False, classes=classes, justify="unset")

    def summary_report_output(
        self, report_data: dict[str, Any], classes: list[str]
    ) -> dict[str, str]:
        summary = {
            k: v
            for k, v in report_data.items()
            if k not in ["vendor_breakdown", "duplicates_report", "call_number_issues"]
        }
        summary_df = pd.DataFrame(data=summary)
        summary_df = summary_df.T
        return {
            "summary_report": summary_df.to_html(
                header=False, classes=classes, justify="unset"
            ),
            "vendor_report": self.report_to_html(
                report_data["vendor_breakdown"], classes=classes
            ),
            "call_no_report": self.report_to_html(
                report_data["call_number_issues"], classes=classes
            ),
            "dupe_report": self.report_to_html(
                report_data["duplicates_report"], classes=classes
            ),
        }


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

    def write_report(self, data: list[list[Any]]) -> None:
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
        try:
            service = build("sheets", "v4", credentials=self.creds)
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
        logger.error("Data not written to sheet.")

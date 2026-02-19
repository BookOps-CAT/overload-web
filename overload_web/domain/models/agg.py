from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from overload_web.domain.models import bibs, reports


@dataclass
class MarcFile:
    id: str
    file_name: str
    uploaded_at: datetime
    domain_bibs: List[bibs.DomainBib] = field(default_factory=list)
    statistics: reports.ProcessingStatistics | None = None
    output_files: List["OutputFile"] = field(default_factory=list)

    # Domain behavior
    def process(self, handler: "ProcessingHandler"):
        for bib in self.domain_bibs:
            matches = handler.match_service.match_full_record(bib)
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
        # deduplication, statistics, output_files
        self.statistics = self.compute_statistics()
        self.output_files = self.generate_output_files()

    def compute_statistics(self) -> reports.ProcessingStatistics:
        # calculate counts, duplicates, missing barcodes, etc.
        ...

    def generate_output_files(self) -> List["OutputFile"]:
        # serialize MARC records, write to disk, return OutputFile references
        ...

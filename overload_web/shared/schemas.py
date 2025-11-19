"""Shared schemas to be used by multiple layers of application"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FileData:
    content: bytes
    file_name: str


@dataclass
class Matchpoints:
    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None

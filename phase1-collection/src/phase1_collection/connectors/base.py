from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from phase1_collection.collection_mode import CollectionMode
from phase1_collection.db import RawFeedbackItem
from phase1_collection.validation import HealthCheckResult, validate_raw_item


class BaseConnector(ABC):
    source_name: str

    @abstractmethod
    def collect(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode = CollectionMode.WEEKLY,
    ) -> list[RawFeedbackItem]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        raise NotImplementedError

    def normalize_item(
        self,
        source_item_id: str,
        posted_at: datetime | None,
        text: str,
        extra: dict | None = None,
    ) -> RawFeedbackItem:
        payload = {
            "source": self.source_name,
            "source_item_id": source_item_id,
            "text": text,
            **(extra or {}),
        }
        validate_raw_item(self.source_name, source_item_id, payload)
        return RawFeedbackItem(
            source_item_id=source_item_id,
            posted_at=posted_at,
            raw_payload=payload,
        )

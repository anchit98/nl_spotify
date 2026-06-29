from __future__ import annotations

from phase1_collection.config import Settings
from phase1_collection.connectors.app_store import AppStoreConnector
from phase1_collection.connectors.base import BaseConnector
from phase1_collection.connectors.community_forum import CommunityForumConnector
from phase1_collection.connectors.google_play import GooglePlayConnector
from phase1_collection.connectors.reddit import RedditConnector
from phase1_collection.connectors.social_media import SocialMediaConnector

CONNECTOR_BUILDERS = {
    "app_store": lambda s: AppStoreConnector(s),
    "google_play": lambda s: GooglePlayConnector(s),
    "reddit": lambda s: RedditConnector(s),
    "community_forum": lambda s: CommunityForumConnector(s),
    "social_media": lambda s: SocialMediaConnector(s),
}


def get_connector(source: str, settings: Settings) -> BaseConnector:
    if source not in CONNECTOR_BUILDERS:
        raise ValueError(f"Unknown source: {source}")
    return CONNECTOR_BUILDERS[source](settings)

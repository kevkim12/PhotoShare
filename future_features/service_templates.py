"""Service templates for future PhotoShare features.

These classes keep future business logic in Python so routes can stay small.
They are safe to import today because they do not touch Flask globals, open
database connections, or mutate application state.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Sequence


@dataclass(frozen=True)
class FeedEvent:
    """A normalized activity item for a future feed page."""

    event_type: str
    actor_email: str
    target_label: str
    target_url: str
    created_at: datetime
    score: int = 0

    def day_key(self) -> date:
        return self.created_at.date()

    def label(self) -> str:
        verbs = {
            "upload": "uploaded",
            "comment": "commented on",
            "like": "liked",
            "friend": "connected with",
        }
        verb = verbs.get(self.event_type, self.event_type.replace("_", " "))
        return f"{self.actor_email} {verb} {self.target_label}"


@dataclass(frozen=True)
class NotificationDraft:
    """A notification before it is written to a future Notifications table."""

    user_id: int
    actor_user_id: int | None
    notification_type: str
    target_id: int | None
    body: str

    def dedupe_key(self) -> tuple[int, int | None, str, int | None]:
        return (self.user_id, self.actor_user_id, self.notification_type, self.target_id)

    def is_self_notification(self) -> bool:
        return self.actor_user_id is not None and self.actor_user_id == self.user_id


@dataclass(frozen=True)
class PhotoSignal:
    """Engagement signals for a photo insights feature."""

    picture_id: int
    caption: str
    like_count: int = 0
    comment_count: int = 0
    tag_count: int = 0
    shared_tag_count: int = 0

    def engagement_score(self) -> float:
        return (
            float(self.like_count * 3)
            + float(self.comment_count * 2)
            + float(self.tag_count)
            + float(self.shared_tag_count) * 1.5
        )

    def recommendation_score(self) -> float:
        base_score = self.engagement_score()
        if self.shared_tag_count:
            base_score += min(self.shared_tag_count, 6) * 2
        return base_score


class ActivityFeedTemplate:
    """Utility behavior for a future activity feed service."""

    DEFAULT_LIMIT = 30

    def __init__(self, events: Iterable[FeedEvent] = ()):
        self.events = list(events)

    def newest_first(self, limit: int | None = None) -> list[FeedEvent]:
        selected_limit = limit or self.DEFAULT_LIMIT
        return sorted(
            self.events,
            key=lambda event: (event.created_at, event.score),
            reverse=True,
        )[:selected_limit]

    def grouped_by_day(self, limit: int | None = None) -> list[dict[str, object]]:
        groups: dict[date, list[FeedEvent]] = defaultdict(list)
        for event in self.newest_first(limit):
            groups[event.day_key()].append(event)
        return [
            {"date": group_date, "events": day_events}
            for group_date, day_events in sorted(groups.items(), reverse=True)
        ]

    def compact_rows(self, limit: int | None = None) -> list[dict[str, object]]:
        return [
            {
                "label": event.label(),
                "url": event.target_url,
                "type": event.event_type,
                "created_at": event.created_at,
            }
            for event in self.newest_first(limit)
        ]

    def empty_state(self) -> dict[str, str]:
        return {
            "title": "No activity yet",
            "body": "Upload photos, add friends, or comment on photos to start building an activity feed.",
        }


class NotificationTemplate:
    """Draft generation helpers for a future notification center."""

    DEFAULT_TYPES = {"comment", "like", "friend", "recommendation", "album_share"}

    def __init__(self, allowed_types: Iterable[str] | None = None):
        self.allowed_types = set(allowed_types or self.DEFAULT_TYPES)

    def validate(self, draft: NotificationDraft) -> bool:
        return (
            draft.notification_type in self.allowed_types
            and bool(draft.body.strip())
            and not draft.is_self_notification()
        )

    def dedupe(self, drafts: Iterable[NotificationDraft]) -> list[NotificationDraft]:
        deduped: dict[tuple[int, int | None, str, int | None], NotificationDraft] = {}
        for draft in drafts:
            if self.validate(draft):
                deduped[draft.dedupe_key()] = draft
        return list(deduped.values())

    def for_comment(
        self,
        owner_user_id: int,
        commenter_user_id: int,
        picture_id: int,
        commenter_label: str,
    ) -> NotificationDraft:
        return NotificationDraft(
            user_id=owner_user_id,
            actor_user_id=commenter_user_id,
            notification_type="comment",
            target_id=picture_id,
            body=f"{commenter_label} commented on your photo.",
        )

    def for_like(
        self,
        owner_user_id: int,
        liking_user_id: int,
        picture_id: int,
        liker_label: str,
    ) -> NotificationDraft:
        return NotificationDraft(
            user_id=owner_user_id,
            actor_user_id=liking_user_id,
            notification_type="like",
            target_id=picture_id,
            body=f"{liker_label} liked your photo.",
        )

    def digest_preview(self, drafts: Sequence[NotificationDraft], max_items: int = 5) -> dict[str, object]:
        valid_drafts = self.dedupe(drafts)
        return {
            "count": len(valid_drafts),
            "items": valid_drafts[:max_items],
            "has_more": len(valid_drafts) > max_items,
        }


class SearchFilterTemplate:
    """Build safe, reusable search state before SQL is assembled by a route."""

    VALID_MODES = {"tag", "comment", "caption", "album"}

    def normalize_mode(self, mode: str) -> str:
        normalized = mode.lower().strip()
        if normalized not in self.VALID_MODES:
            raise ValueError(f"Unsupported search mode: {mode}")
        return normalized

    def normalize_terms(self, raw_terms: str | Iterable[str]) -> tuple[str, ...]:
        if isinstance(raw_terms, str):
            pieces = raw_terms.replace(",", " ").split()
        else:
            pieces = list(raw_terms)
        return tuple(
            sorted(
                {
                    piece.strip().lower()
                    for piece in pieces
                    if piece and piece.strip()
                }
            )
        )

    def state(self, mode: str, raw_terms: str | Iterable[str]) -> dict[str, object]:
        terms = self.normalize_terms(raw_terms)
        return {
            "mode": self.normalize_mode(mode),
            "terms": terms,
            "label": self.label_for(mode, terms),
            "is_empty": len(terms) == 0,
        }

    def label_for(self, mode: str, terms: Iterable[str]) -> str:
        normalized_mode = self.normalize_mode(mode)
        normalized_terms = tuple(terms)
        if not normalized_terms:
            return f"Empty {normalized_mode} search"
        return f"{normalized_mode.title()}: {', '.join(normalized_terms)}"

    def query_shape(self, mode: str) -> dict[str, str]:
        normalized = self.normalize_mode(mode)
        shapes = {
            "tag": {
                "table": "Associate",
                "column": "word",
                "join": "JOIN Pictures p ON p.picture_id = Associate.picture_id",
            },
            "comment": {
                "table": "Comments",
                "column": "text",
                "join": "JOIN Has h ON h.comment_id = Comments.comment_id",
            },
            "caption": {
                "table": "Pictures",
                "column": "caption",
                "join": "",
            },
            "album": {
                "table": "Albums",
                "column": "albumname",
                "join": "",
            },
        }
        return shapes[normalized]


class PhotoInsightsTemplate:
    """Analytics helpers that can back a future insights page."""

    def rank_by_engagement(self, signals: Iterable[PhotoSignal], limit: int = 10) -> list[PhotoSignal]:
        return sorted(
            signals,
            key=lambda signal: (signal.engagement_score(), signal.like_count, signal.comment_count),
            reverse=True,
        )[:limit]

    def rank_by_recommendation(self, signals: Iterable[PhotoSignal], limit: int = 10) -> list[PhotoSignal]:
        return sorted(
            signals,
            key=lambda signal: (signal.recommendation_score(), signal.shared_tag_count),
            reverse=True,
        )[:limit]

    def totals(self, signals: Iterable[PhotoSignal]) -> dict[str, float]:
        signal_list = list(signals)
        photo_count = len(signal_list)
        like_count = sum(signal.like_count for signal in signal_list)
        comment_count = sum(signal.comment_count for signal in signal_list)
        tag_count = sum(signal.tag_count for signal in signal_list)
        return {
            "photo_count": photo_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "tag_count": tag_count,
            "average_likes": like_count / photo_count if photo_count else 0.0,
            "average_comments": comment_count / photo_count if photo_count else 0.0,
        }

    def caption_suggestions(self, signal: PhotoSignal) -> list[str]:
        suggestions: list[str] = []
        if signal.tag_count == 0:
            suggestions.append("Add tags so this photo can appear in tag search and recommendations.")
        if signal.comment_count == 0:
            suggestions.append("Ask a question in the caption to invite comments.")
        if signal.like_count == 0:
            suggestions.append("Share the album with friends to collect the first likes.")
        return suggestions

    def insight_rows(self, signals: Iterable[PhotoSignal]) -> list[dict[str, object]]:
        return [
            {
                "picture_id": signal.picture_id,
                "caption": signal.caption,
                "likes": signal.like_count,
                "comments": signal.comment_count,
                "tags": signal.tag_count,
                "engagement_score": round(signal.engagement_score(), 2),
                "recommendation_score": round(signal.recommendation_score(), 2),
                "suggestions": self.caption_suggestions(signal),
            }
            for signal in self.rank_by_engagement(signals)
        ]

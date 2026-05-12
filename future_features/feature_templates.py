"""Planning templates for future PhotoShare feature updates.

The current application keeps most behavior in ``app.py``. These templates give
future work a Python-first place to sketch feature routes, supporting queries,
and rollout notes before those pieces are connected to Flask views.
"""

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class RouteTemplate:
    """A lightweight description of a Flask route that may be added later."""

    endpoint: str
    methods: tuple[str, ...]
    template_name: str
    auth_required: bool = True
    nav_label: str | None = None

    def decorator_preview(self) -> str:
        methods = ", ".join(repr(method) for method in self.methods)
        return f"@app.route('{self.endpoint}', methods=[{methods}])"

    def navigation_item(self) -> dict[str, str]:
        label = self.nav_label or self.endpoint.strip("/").replace("-", " ").title()
        return {"label": label, "href": self.endpoint}


@dataclass(frozen=True)
class QueryTemplate:
    """Stores a named SQL sketch and the parameters a future handler needs."""

    name: str
    sql: str
    parameters: tuple[str, ...] = ()
    returns_many: bool = True

    def parameter_help(self) -> str:
        if not self.parameters:
            return "No parameters required."
        return "Requires: " + ", ".join(self.parameters)


@dataclass(frozen=True)
class FeatureTemplate:
    """A reusable blueprint for a future feature."""

    slug: str
    title: str
    summary: str
    routes: tuple[RouteTemplate, ...] = ()
    queries: tuple[QueryTemplate, ...] = ()
    tags: tuple[str, ...] = ()
    rollout_steps: tuple[str, ...] = ()
    database_notes: tuple[str, ...] = ()
    ui_notes: tuple[str, ...] = ()

    def route_names(self) -> tuple[str, ...]:
        return tuple(route.endpoint for route in self.routes)

    def query_names(self) -> tuple[str, ...]:
        return tuple(query.name for query in self.queries)

    def matches(self, search_text: str) -> bool:
        normalized = search_text.lower().strip()
        searchable = " ".join((self.slug, self.title, self.summary, *self.tags)).lower()
        return normalized in searchable

    def as_card(self) -> dict[str, object]:
        return {
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "routes": list(self.route_names()),
            "tags": list(self.tags),
        }


class FutureFeatureCatalog:
    """Read-only registry for feature templates."""

    def __init__(self, features: Iterable[FeatureTemplate]):
        self._features = {feature.slug: feature for feature in features}

    def __iter__(self):
        return iter(self._features.values())

    def list_slugs(self) -> tuple[str, ...]:
        return tuple(sorted(self._features))

    def get(self, slug: str) -> FeatureTemplate:
        try:
            return self._features[slug]
        except KeyError as exc:
            available = ", ".join(self.list_slugs())
            raise KeyError(f"Unknown future feature '{slug}'. Available: {available}") from exc

    def search(self, search_text: str) -> tuple[FeatureTemplate, ...]:
        return tuple(feature for feature in self if feature.matches(search_text))

    def by_tag(self, tag: str) -> tuple[FeatureTemplate, ...]:
        normalized = tag.lower().strip()
        return tuple(
            feature
            for feature in self
            if any(feature_tag.lower() == normalized for feature_tag in feature.tags)
        )

    def routes_for(self, slug: str) -> tuple[RouteTemplate, ...]:
        return self.get(slug).routes

    def queries_for(self, slug: str) -> tuple[QueryTemplate, ...]:
        return self.get(slug).queries

    def database_notes(self) -> dict[str, tuple[str, ...]]:
        return {
            feature.slug: feature.database_notes
            for feature in self
            if feature.database_notes
        }

    def navigation_cards(self) -> list[dict[str, object]]:
        return [feature.as_card() for feature in sorted(self, key=lambda item: item.title)]

    def route_table(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for feature in self:
            for route in feature.routes:
                rows.append(
                    {
                        "feature": feature.slug,
                        "endpoint": route.endpoint,
                        "methods": route.methods,
                        "template": route.template_name,
                        "auth_required": route.auth_required,
                    }
                )
        return rows


DEFAULT_FEATURES: tuple[FeatureTemplate, ...] = (
    FeatureTemplate(
        slug="activity-feed",
        title="Activity Feed",
        summary="A personalized stream of uploads, comments, likes, and friend activity.",
        tags=("social", "engagement", "dashboard"),
        routes=(
            RouteTemplate("/activity", ("GET",), "activity.html", nav_label="Activity"),
            RouteTemplate("/activity/mark-read", ("POST",), "activity.html"),
        ),
        queries=(
            QueryTemplate(
                name="recent_friend_uploads",
                sql="""
                    SELECT p.picture_id, p.caption, a.albumname, u.email
                    FROM Friends f
                    JOIN Pictures p ON p.user_id = f.user_id2
                    JOIN Users u ON u.user_id = p.user_id
                    LEFT JOIN Contains c ON c.picture_id = p.picture_id
                    LEFT JOIN Albums a ON a.album_id = c.album_id
                    WHERE f.user_id1 = %s
                    ORDER BY p.picture_id DESC
                    LIMIT %s
                """.strip(),
                parameters=("current_user_id", "limit"),
            ),
            QueryTemplate(
                name="recent_photo_comments",
                sql="""
                    SELECT c.comment_id, c.text, h.picture_id, made.user_id
                    FROM Comments c
                    JOIN Has h ON h.comment_id = c.comment_id
                    LEFT JOIN Made made ON made.comment_id = c.comment_id
                    WHERE h.picture_id IN ({picture_ids})
                    ORDER BY c.comment_id DESC
                """.strip(),
                parameters=("picture_ids",),
            ),
        ),
        rollout_steps=(
            "Add an activity service that accepts the current user's id.",
            "Create a compact activity template using existing photo-card styles.",
            "Add read-state storage once the stream is useful without it.",
        ),
        database_notes=(
            "A future ActivityReads table can track which events a user has seen.",
            "Existing Friends, Pictures, Comments, Has, Made, and Likes tables provide the first event sources.",
        ),
        ui_notes=(
            "Keep the feed scannable with short labels and small thumbnails.",
            "Group events by date so the page feels useful with many events.",
        ),
    ),
    FeatureTemplate(
        slug="private-albums",
        title="Private Albums",
        summary="Album-level visibility controls for private, friends-only, and public sharing.",
        tags=("privacy", "albums", "sharing"),
        routes=(
            RouteTemplate("/albums/<int:album_id>/privacy", ("GET", "POST"), "album_privacy.html"),
            RouteTemplate("/shared-with-me", ("GET",), "shared_albums.html", nav_label="Shared"),
        ),
        queries=(
            QueryTemplate(
                name="album_visibility",
                sql="""
                    SELECT album_id, albumname, user_id, visibility
                    FROM Albums
                    WHERE album_id = %s
                """.strip(),
                parameters=("album_id",),
                returns_many=False,
            ),
            QueryTemplate(
                name="visible_albums_for_user",
                sql="""
                    SELECT DISTINCT a.album_id, a.albumname, a.user_id
                    FROM Albums a
                    LEFT JOIN Friends f ON f.user_id2 = a.user_id
                    WHERE a.visibility = 'public'
                       OR a.user_id = %s
                       OR (a.visibility = 'friends' AND f.user_id1 = %s)
                """.strip(),
                parameters=("current_user_id", "current_user_id"),
            ),
        ),
        rollout_steps=(
            "Add a visibility column with a safe public default for current albums.",
            "Centralize album access checks before changing route behavior.",
            "Update public browsing to call the shared access helper.",
        ),
        database_notes=(
            "Albums.visibility can start as TEXT with public, friends, and private values.",
            "A later AlbumShares table could allow direct sharing with selected users.",
        ),
        ui_notes=(
            "Use a simple segmented control for visibility choices.",
            "Show visibility labels on album management pages.",
        ),
    ),
    FeatureTemplate(
        slug="saved-searches",
        title="Saved Searches",
        summary="Let users save tag and comment searches and revisit them from the profile page.",
        tags=("search", "profile", "productivity"),
        routes=(
            RouteTemplate("/saved-searches", ("GET",), "saved_searches.html", nav_label="Saved Searches"),
            RouteTemplate("/saved-searches", ("POST",), "saved_searches.html"),
            RouteTemplate("/saved-searches/<int:search_id>/delete", ("POST",), "saved_searches.html"),
        ),
        queries=(
            QueryTemplate(
                name="saved_searches_for_user",
                sql="""
                    SELECT search_id, label, search_type, search_text, created_at
                    FROM SavedSearches
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """.strip(),
                parameters=("current_user_id",),
            ),
            QueryTemplate(
                name="create_saved_search",
                sql="""
                    INSERT INTO SavedSearches (user_id, label, search_type, search_text, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """.strip(),
                parameters=("current_user_id", "label", "search_type", "search_text"),
                returns_many=False,
            ),
        ),
        rollout_steps=(
            "Add the SavedSearches table and a small validation helper.",
            "Offer save actions after successful tag and comment searches.",
            "Render saved searches as quick links on the profile dashboard.",
        ),
        database_notes=(
            "SavedSearches should store user_id, label, search_type, search_text, and created_at.",
            "Limit search_type to known search modes before inserting rows.",
        ),
        ui_notes=(
            "Keep saved search labels editable later, but start with automatic labels.",
            "Reuse the existing search forms so the feature feels native.",
        ),
    ),
    FeatureTemplate(
        slug="notification-center",
        title="Notification Center",
        summary="A small inbox for likes, comments, recommendations, and friend actions.",
        tags=("social", "notifications", "engagement"),
        routes=(
            RouteTemplate("/notifications", ("GET",), "notifications.html", nav_label="Notifications"),
            RouteTemplate("/notifications/<int:notification_id>/read", ("POST",), "notifications.html"),
        ),
        queries=(
            QueryTemplate(
                name="unread_notifications",
                sql="""
                    SELECT notification_id, actor_user_id, notification_type, target_id, body, created_at
                    FROM Notifications
                    WHERE user_id = %s AND read_at IS NULL
                    ORDER BY created_at DESC
                """.strip(),
                parameters=("current_user_id",),
            ),
            QueryTemplate(
                name="mark_notification_read",
                sql="""
                    UPDATE Notifications
                    SET read_at = CURRENT_TIMESTAMP
                    WHERE notification_id = %s AND user_id = %s
                """.strip(),
                parameters=("notification_id", "current_user_id"),
                returns_many=False,
            ),
        ),
        rollout_steps=(
            "Generate notification drafts in comment, like, and friend flows.",
            "Persist only user-visible events to avoid noisy inboxes.",
            "Add unread counts after the basic inbox is stable.",
        ),
        database_notes=(
            "Notifications can store actor_user_id, user_id, notification_type, target_id, body, created_at, and read_at.",
            "Use target_id with notification_type to link back to a photo, album, or profile.",
        ),
        ui_notes=(
            "Use short notification rows rather than large cards.",
            "Keep read and unread states visually distinct but restrained.",
        ),
    ),
    FeatureTemplate(
        slug="photo-insights",
        title="Photo Insights",
        summary="Owner-facing analytics for likes, comments, tags, and recommendation signals.",
        tags=("analytics", "photos", "dashboard"),
        routes=(
            RouteTemplate("/insights", ("GET",), "photo_insights.html", nav_label="Insights"),
            RouteTemplate("/insights/<int:picture_id>", ("GET",), "photo_insight_detail.html"),
        ),
        queries=(
            QueryTemplate(
                name="photo_engagement",
                sql="""
                    SELECT p.picture_id, p.caption,
                           COUNT(DISTINCT l.user_id) AS like_count,
                           COUNT(DISTINCT h.comment_id) AS comment_count,
                           COUNT(DISTINCT assoc.word) AS tag_count
                    FROM Pictures p
                    LEFT JOIN Likes l ON l.picture_id = p.picture_id
                    LEFT JOIN Has h ON h.picture_id = p.picture_id
                    LEFT JOIN Associate assoc ON assoc.picture_id = p.picture_id
                    WHERE p.user_id = %s
                    GROUP BY p.picture_id, p.caption
                    ORDER BY like_count DESC, comment_count DESC
                """.strip(),
                parameters=("current_user_id",),
            ),
            QueryTemplate(
                name="top_owner_tags",
                sql="""
                    SELECT assoc.word, COUNT(*) AS photo_count
                    FROM Pictures p
                    JOIN Associate assoc ON assoc.picture_id = p.picture_id
                    WHERE p.user_id = %s
                    GROUP BY assoc.word
                    ORDER BY photo_count DESC, assoc.word ASC
                """.strip(),
                parameters=("current_user_id",),
            ),
        ),
        rollout_steps=(
            "Build a pure Python insights service before adding charts.",
            "Expose simple totals first, then add trend views if timestamps are available.",
            "Link insight rows back to the existing photo detail page.",
        ),
        database_notes=(
            "The existing schema supports aggregate insights without new tables.",
            "A future PhotoViews table would make view counts and trends possible.",
        ),
        ui_notes=(
            "Favor tables and compact metrics over decorative dashboards.",
            "Use existing leaderboard styling for consistency.",
        ),
    ),
)


def default_feature_catalog() -> FutureFeatureCatalog:
    """Return the standard future feature catalog."""

    return FutureFeatureCatalog(DEFAULT_FEATURES)


def feature_lookup_by_route(catalog: FutureFeatureCatalog | None = None) -> Mapping[str, str]:
    """Map proposed route endpoints to the feature slug that owns them."""

    active_catalog = catalog or default_feature_catalog()
    lookup: dict[str, str] = {}
    for feature in active_catalog:
        for route in feature.routes:
            lookup[route.endpoint] = feature.slug
    return lookup

"""Future-facing Python templates for PhotoShare feature work.

These modules are intentionally not wired into the Flask app yet. They collect
small service and route-planning patterns that can be promoted into real
features when the project is ready for the next iteration.
"""

from .feature_templates import (
    FeatureTemplate,
    FutureFeatureCatalog,
    QueryTemplate,
    RouteTemplate,
    default_feature_catalog,
)
from .service_templates import (
    ActivityFeedTemplate,
    FeedEvent,
    NotificationDraft,
    NotificationTemplate,
    PhotoInsightsTemplate,
    PhotoSignal,
    SearchFilterTemplate,
)

__all__ = [
    "ActivityFeedTemplate",
    "FeatureTemplate",
    "FeedEvent",
    "FutureFeatureCatalog",
    "NotificationDraft",
    "NotificationTemplate",
    "PhotoInsightsTemplate",
    "PhotoSignal",
    "QueryTemplate",
    "RouteTemplate",
    "SearchFilterTemplate",
    "default_feature_catalog",
]

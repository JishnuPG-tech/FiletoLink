"""Mutation contracts, rollback specifications, and disabled tool definitions for Stage 2."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# Maximum bounded payload sizes for snapshots
MAX_METADATA_SNAPSHOT_BYTES = 64 * 1024       # 64 KB
MAX_IMAGE_SNAPSHOT_BYTES = 15 * 1024 * 1024   # 15 MB
MAX_SUBTITLE_SNAPSHOT_BYTES = 3 * 1024 * 1024  # 3 MB

# Fields restorable via Jellyfin item metadata update
RESTORABLE_METADATA_FIELDS: Set[str] = {
    "Name",
    "OriginalTitle",
    "Overview",
    "Genres",
    "ProductionYear",
    "ProviderIds",
    "CommunityRating",
    "OfficialRating",
    "Taglines",
    "Studios",
}

# Fields that can NEVER be modified or overwritten during rollback
PROTECTED_IMMUTABLE_FIELDS: Set[str] = {
    "Id",
    "Path",
    "Container",
    "MediaSources",
    "MediaStreams",
    "DateCreated",
}


@dataclass
class MutationContract:
    """Explicit specification for a mutating operation, its pre-flight snapshot, and rollback guarantee."""
    tool_name: str
    target_entity: str                 # "jellyfin_item_metadata" | "jellyfin_artwork" | "jellyfin_subtitle" | "jellyfin_library"
    requires_snapshot: bool
    requires_confirmation: bool
    is_reversible: bool
    allowed_fields: Set[str] = field(default_factory=set)
    max_payload_bytes: int = MAX_METADATA_SNAPSHOT_BYTES
    failure_policy: str = "fail_closed_audit_alert"


MUTATION_CONTRACTS: Dict[str, MutationContract] = {
    "jellyfin_refresh_item": MutationContract(
        tool_name="jellyfin_refresh_item",
        target_entity="jellyfin_library",
        requires_snapshot=False,
        requires_confirmation=True,
        is_reversible=False,
        failure_policy="log_warning_no_disk_mutation",
    ),
    "jellyfin_update_metadata": MutationContract(
        tool_name="jellyfin_update_metadata",
        target_entity="jellyfin_item_metadata",
        requires_snapshot=True,
        requires_confirmation=True,
        is_reversible=True,
        allowed_fields=RESTORABLE_METADATA_FIELDS,
        max_payload_bytes=MAX_METADATA_SNAPSHOT_BYTES,
        failure_policy="atomic_rollback_or_alert",
    ),
    "apply_image": MutationContract(
        tool_name="apply_image",
        target_entity="jellyfin_artwork",
        requires_snapshot=True,
        requires_confirmation=True,
        is_reversible=True,
        max_payload_bytes=MAX_IMAGE_SNAPSHOT_BYTES,
        failure_policy="atomic_rollback_or_alert",
    ),
    "apply_subtitle": MutationContract(
        tool_name="apply_subtitle",
        target_entity="jellyfin_subtitle",
        requires_snapshot=True,
        requires_confirmation=True,
        is_reversible=True,
        max_payload_bytes=MAX_SUBTITLE_SNAPSHOT_BYTES,
        failure_policy="atomic_rollback_or_alert",
    ),
    "revert_last_change": MutationContract(
        tool_name="revert_last_change",
        target_entity="snapshot_history",
        requires_snapshot=False,
        requires_confirmation=True,
        is_reversible=False,
        failure_policy="fail_closed_report_discrepancy",
    ),
}


# ==============================================================================
# Incomplete Rollback Handling Policy
# ==============================================================================
# When an item restoration is attempted but encounters a partial failure (e.g.
# Jellyfin accepts Overview but rejects ProviderIds, or sidecar deletion fails):
# 1. Verification Outcome: Recorded as `verification_result="partial_failure"`.
# 2. Audit Trail: The exact difference between the expected snapshot and current
#    item state is written to the audit log `params_summary` (with secret scrubbing).
# 3. Notification: The admin is alerted with the snapshot ID and specific fields.
# 4. Safe State: The runner never retries destructive file deletions on ambiguity.

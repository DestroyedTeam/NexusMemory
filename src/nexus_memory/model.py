"""Loss-aware, vendor-neutral Canonical Domain Model (v2, backwards-compatible with v1).

Separates distinct concepts instead of conflating them:
- Account / Workspace / Host / AppMode (standard vs Claude-3p vs CLI)
- Sidebar Section Groups (source-qualified membership, distinct from Project containment)
- Projects / Workspaces / Repositories
- Sessions / Conversations / Threads with UsageSummary, Links, Archive state, and Fork/Subtask edges
- MessageNodes / Events (including tool_use, tool_result, thinking, compaction, interruption, subagent parent_tool_use_id)
- Content-addressed AssetRecords (SHA-256, MIME, size, availability disposition)
- ResourceBundle (Skills, secret-redacted MCP configs, Plugins, Instructions, Memory, Permission hints, Schedules)
- Multi-dimensional FidelityReport & LossItems (never collapsing loss into one opaque score)
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

URL_RE = re.compile(r"https?://[^\s<>\"'`\])\}]+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    reasoning_tokens: int = 0
    total_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_empty(self) -> bool:
        return (
            self.input_tokens == 0
            and self.output_tokens == 0
            and self.cache_read_tokens == 0
            and self.cache_creation_tokens == 0
            and self.reasoning_tokens == 0
            and (self.total_cost_usd is None or self.total_cost_usd == 0)
        )


@dataclass(frozen=True, slots=True)
class AssetRecord:
    asset_id: str
    source_ref: str
    filename: str
    mime_type: str
    sha256: str | None = None
    size_bytes: int | None = None
    disposition: str = "external_reference"  # embedded_copied | external_reference | missing_in_export | skipped_oversize
    relative_bundle_path: str | None = None
    source_node_id: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MessageNode:
    """One node in a conversation DAG.

    First 8 fields preserve positional compatibility with v0.1 prototype callers.
    """

    node_id: str
    parent_id: str | None
    child_ids: tuple[str, ...]
    role: str | None
    text: str
    timestamp: Any
    content: Any
    raw_record: dict[str, Any]
    event_type: str = "message"  # message | user_followup | interruption | tool_use | tool_result | thinking | compaction | system | error | result
    parent_tool_use_id: str | None = None
    attachments: tuple[dict[str, Any], ...] = ()
    links: tuple[str, ...] = ()
    usage: dict[str, Any] | None = None
    interrupted: bool = False
    is_sidechain: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConversationGraph:
    """Lossless canonical session graph with full provenance.

    First 9 fields preserve positional compatibility with v0.1 prototype callers.
    """

    source_format: str
    source_id: str
    title: str | None
    workspace: str | None
    nodes: tuple[MessageNode, ...]
    root_ids: tuple[str, ...]
    active_node_id: str | None
    metadata: dict[str, Any]
    raw_source: dict[str, Any]
    assets: tuple[AssetRecord, ...] = ()
    usage: UsageSummary | None = None
    links: tuple[str, ...] = ()
    app_mode: str | None = None  # e.g. cli | claude-3p-chat | claude-3p-cowork | claude-3p-code | web-export

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fork_points(self) -> list[str]:
        """Return node IDs that have more than one valid child (branch/regeneration points)."""
        by_id = {node.node_id for node in self.nodes}
        return [
            node.node_id
            for node in self.nodes
            if sum(1 for cid in node.child_ids if cid in by_id) > 1
        ]

    def branch_paths(self, *, max_paths: int = 256) -> list[list[MessageNode]]:
        """Return root-to-leaf paths iteratively without flattening source branches.

        Uses an explicit stack with O(N) path/ancestor tracking so deep conversations
        with thousands of turns/tool events never trigger Python's recursion limit.
        """
        by_id = {node.node_id: node for node in self.nodes}
        if len(by_id) != len(self.nodes):
            raise ValueError("conversation contains duplicate node IDs")
        roots = [node_id for node_id in self.root_ids if node_id in by_id]
        if not roots and self.nodes:
            roots = [node.node_id for node in self.nodes if node.parent_id not in by_id]

        paths: list[list[MessageNode]] = []
        reached: set[str] = set()

        for root_id in roots:
            root_node = by_id[root_id]
            reached.add(root_id)
            path: list[MessageNode] = [root_node]
            ancestors: set[str] = {root_id}
            root_children = [c for c in root_node.child_ids if c in by_id]
            stack: list[tuple[str, list[str], int]] = [(root_id, root_children, 0)]

            while stack:
                node_id, children, idx = stack[-1]
                if not children:
                    paths.append(list(path))
                    if len(paths) > max_paths:
                        raise ValueError(f"conversation has more than {max_paths} leaf paths")
                    stack.pop()
                    path.pop()
                    ancestors.remove(node_id)
                    continue

                if idx >= len(children):
                    stack.pop()
                    path.pop()
                    ancestors.remove(node_id)
                    continue

                child_id = children[idx]
                stack[-1] = (node_id, children, idx + 1)
                if child_id in ancestors:
                    raise ValueError(f"conversation graph contains a cycle at {child_id}")
                child_node = by_id[child_id]
                reached.add(child_id)
                path.append(child_node)
                ancestors.add(child_id)
                child_children = [c for c in child_node.child_ids if c in by_id]
                stack.append((child_id, child_children, 0))

        if len(reached) != len(self.nodes):
            missing = sorted(set(by_id) - reached)
            raise ValueError(f"conversation has unreachable or cyclic nodes: {missing[:5]}")
        return paths


@dataclass(frozen=True, slots=True)
class SkillRecord:
    name: str
    source_harness: str
    scope: str  # user | project
    source_path: str
    description: str = ""
    files: tuple[dict[str, Any], ...] = ()  # [{"rel_path": str, "sha256": str, "size_bytes": int}]
    frontmatter: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class McpServerRecord:
    name: str
    source_harness: str
    scope: str  # user | project
    transport: str  # stdio | http | sse | unknown
    command: str | None = None
    args: tuple[str, ...] = ()
    url: str | None = None
    env_keys: tuple[str, ...] = ()  # key names ONLY or non-secret literals; secrets stripped to ${VAR}
    env_template: dict[str, str] = field(default_factory=dict)
    headers_template: dict[str, str] = field(default_factory=dict)
    stripped_secret_keys: tuple[str, ...] = ()
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PluginRecord:
    name: str
    source_harness: str
    scope: str
    enabled: bool | None = None
    version: str | None = None
    source_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InstructionRecord:
    name: str
    source_harness: str
    scope: str
    source_path: str
    sha256: str
    size_bytes: int
    content_redacted: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    name: str
    source_harness: str
    scope: str
    source_path: str
    sha256: str
    size_bytes: int
    preview_redacted: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PermissionHint:
    source_harness: str
    scope: str
    rule: str
    mode: str = "advisory_only_never_auto_granted"
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScheduleRecord:
    name: str
    source_harness: str
    schedule_expr: str
    prompt_redacted: str = ""
    enabled: bool = False  # Migrated disabled by default until user confirms
    source_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResourceBundle:
    skills: tuple[SkillRecord, ...] = ()
    mcp_servers: tuple[McpServerRecord, ...] = ()
    plugins: tuple[PluginRecord, ...] = ()
    instructions: tuple[InstructionRecord, ...] = ()
    memories: tuple[MemoryRecord, ...] = ()
    permission_hints: tuple[PermissionHint, ...] = ()
    schedules: tuple[ScheduleRecord, ...] = ()
    redacted_secret_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary_counts(self) -> dict[str, int]:
        return {
            "skills": len(self.skills),
            "mcp_servers": len(self.mcp_servers),
            "plugins": len(self.plugins),
            "instructions": len(self.instructions),
            "memories": len(self.memories),
            "permission_hints": len(self.permission_hints),
            "schedules": len(self.schedules),
        }


@dataclass(frozen=True, slots=True)
class LossItem:
    feature: str
    disposition: str  # preserved_natively | projected_degraded | archived_sidecar_only | dropped_security_policy | unsupported_unknown
    source_id: str | None = None
    source_node_id: str | None = None
    target_capability: str | None = None
    reason: str | None = None
    confidence: str = "verified_schema"

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True, slots=True)
class FidelityReport:
    """Multi-dimensional fidelity coverage — never hides losses behind one fake score."""

    target: str
    structural_fidelity: dict[str, Any]
    message_event_fidelity: dict[str, Any]
    branch_subtask_fidelity: dict[str, Any]
    asset_fidelity: dict[str, Any]
    resource_plane_fidelity: dict[str, Any]
    native_resume_readiness: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class HarnessDescriptor:
    """Explicit capability descriptor per Harness/lane (adapted from SourceDescriptor pattern)."""

    id: str
    display_name: str
    family: str
    surface: str  # cli | desktop-3p | desktop-standard | ide-extension | web-export | canonical
    evidence_level: str  # E0..E6
    read_supported: bool
    write_supported: bool
    native_branch_dag: bool
    native_projects: bool
    native_sections: bool
    native_tool_events: bool
    native_attachments: bool
    native_skills: bool
    native_mcp: bool
    skill_deploy_mode: str = "copy"  # copy | symlink_or_copy
    api_key_gateway_compatible: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def content_text(value: Any) -> str:
    """Extract readable text iteratively while the original typed content remains in `content`."""
    if isinstance(value, str):
        return value
    chunks: list[str] = []
    stack: list[Any] = [value]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            if cur:
                chunks.append(cur)
        elif isinstance(cur, list):
            for part in reversed(cur):
                stack.append(part)
        elif isinstance(cur, dict):
            direct = cur.get("text")
            if isinstance(direct, str):
                if direct:
                    chunks.append(direct)
                continue
            parts = cur.get("parts")
            if isinstance(parts, list):
                for part in reversed(parts):
                    stack.append(part)
                continue
            thinking = cur.get("thinking")
            if isinstance(thinking, str) and cur.get("type") == "thinking":
                if thinking:
                    chunks.append(thinking)
                continue
            content = cur.get("content")
            if isinstance(content, (str, list)):
                stack.append(content)
    return "\n".join(chunks)


def extract_links(value: Any) -> tuple[str, ...]:
    """Deterministically extract unique http(s) URLs from text or structured content."""
    text = value if isinstance(value, str) else content_text(value)
    if not text:
        return ()
    seen: list[str] = []
    seen_set: set[str] = set()
    for match in URL_RE.findall(text):
        cleaned = match.rstrip(".,;:!?)")
        if cleaned and cleaned not in seen_set:
            seen_set.add(cleaned)
            seen.append(cleaned)
    return tuple(seen)

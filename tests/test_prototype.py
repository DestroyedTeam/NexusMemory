from __future__ import annotations

import json
import re
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path

from nexus_memory.bundle import build_hierarchy, preview, write_bundle
from nexus_memory.chatgpt import parse_export
from nexus_memory.claude_code import build_native_sessions, encode_jsonl, project_directory_name
from nexus_memory.codex import parse_rollout
from nexus_memory.model import ConversationGraph
from nexus_memory.security import scan_secret_markers

ROOT = Path(__file__).parent


class PrototypeTests(unittest.TestCase):
    def test_chatgpt_mapping_retains_branch_graph_and_active_node(self) -> None:
        graphs = parse_export(ROOT / "fixtures/chatgpt_branch_export.json")
        self.assertEqual(len(graphs), 1)
        graph = graphs[0]
        self.assertEqual(graph.metadata["project_name"], "Synthetic Project")
        self.assertEqual(graph.metadata["section_name"], "Synthetic Group")
        self.assertEqual(graph.active_node_id, "assistant-leaf-a")
        hierarchy = build_hierarchy(graphs)
        self.assertEqual(hierarchy["projects"][0]["source_id"], "fixture-project-7")
        self.assertEqual(hierarchy["section_groups"][0]["source_id"], "fixture-section-2")
        self.assertEqual(len(hierarchy["projects"][0]["session_refs"]), 1)
        paths = graph.branch_paths()
        self.assertEqual(len(paths), 2)
        self.assertEqual({path[-1].node_id for path in paths}, {"assistant-leaf-a", "assistant-leaf-b"})
        self.assertIn("mapping", graph.raw_source)

    def test_chatgpt_zip_export_reads_conversations_json_without_extracting(self) -> None:
        fixture = ROOT / "fixtures/chatgpt_branch_export.json"
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "export.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.write(fixture, "data/conversations.json")
            graphs = parse_export(archive_path)
        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].source_id, "fixture-chatgpt-001")

    def test_cycle_is_rejected_instead_of_hanging_or_flattening(self) -> None:
        graph = ConversationGraph(
            source_format="fixture",
            source_id="cycle",
            title=None,
            workspace=None,
            nodes=(
                _node("a", "b", ("b",)),
                _node("b", "a", ("a",)),
            ),
            root_ids=(),
            active_node_id=None,
            metadata={},
            raw_source={},
        )
        with self.assertRaisesRegex(ValueError, "unreachable or cyclic"):
            graph.branch_paths()

    def test_codex_rollout_preserves_all_source_records_and_parent_session(self) -> None:
        graph = parse_rollout(ROOT / "fixtures/codex_rollout.jsonl")
        self.assertEqual(graph.source_id, "fixture-codex-001")
        self.assertEqual(graph.metadata["parent_session_id"], "fixture-parent-1")
        self.assertEqual(graph.metadata["record_count"], 6)
        self.assertEqual(len(graph.raw_source["records"]), 6)
        self.assertEqual([node.role for node in graph.nodes], ["user", "tool_call", "tool_result", "assistant"])
        hierarchy = build_hierarchy([graph])
        self.assertEqual(hierarchy["projects"][0]["identity_source"], "workspace_path_inference")
        self.assertEqual(hierarchy["unknown_section_count"], 1)
        self.assertEqual(hierarchy["session_relations"][0]["parent_resolved"], False)

    def test_claude_projection_creates_one_resumable_transcript_per_branch(self) -> None:
        graph = parse_export(ROOT / "fixtures/chatgpt_branch_export.json")[0]
        sessions, losses = build_native_sessions(graph, cwd="/tmp/fixture-project")
        self.assertEqual(len(sessions), 2)
        self.assertTrue(any(loss["feature"] == "branch_topology" for loss in losses))
        attachment_losses = [loss for loss in losses if loss["feature"] == "typed_content_blocks_or_attachments"]
        self.assertEqual(len(attachment_losses), 1)
        self.assertEqual(attachment_losses[0]["source_node_id"], "assistant-leaf-b")
        for session in sessions:
            encoded = encode_jsonl(session["records"]).decode()
            rows = [json.loads(line) for line in encoded.splitlines()]
            self.assertTrue(all(row.get("sessionId") == session["session_id"] for row in rows))
            self.assertEqual(rows[0]["parentUuid"], None)
            self.assertEqual(rows[-1]["type"], "custom-title")

    def test_bundle_is_explicit_and_refuses_overwrite(self) -> None:
        graph = parse_export(ROOT / "fixtures/chatgpt_branch_export.json")[0]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            manifest = write_bundle([graph], out=output, cwd="/tmp/fixture-project")
            self.assertEqual(manifest["native_session_count"], 2)
            self.assertEqual(manifest["project_index_summary"]["project_count"], 1)
            self.assertTrue((output / "portable.json").is_file())
            portable = json.loads((output / "portable.json").read_text())
            self.assertEqual(portable["hierarchy"]["section_groups"][0]["name"], "Synthetic Group")
            self.assertEqual(len(list((output / "claude_sessions").rglob("*.jsonl"))), 2)
            for session in manifest["target_sessions"]:
                target = output / session["target_relative_path"]
                self.assertTrue(target.is_file())
                records = [json.loads(line) for line in target.read_text().splitlines()]
                self.assertTrue(all(record.get("sessionId") == session["session_id"] for record in records))
            with self.assertRaises(FileExistsError):
                write_bundle([graph], out=output, cwd="/tmp/fixture-project")

    def test_codex_workspaces_map_to_separate_claude_projects(self) -> None:
        graph = parse_rollout(ROOT / "fixtures/codex_rollout.jsonl")
        graphs = [
            replace(graph, source_id="codex-one", workspace="/tmp/nexus-workspace-one"),
            replace(graph, source_id="codex-two", workspace="/tmp/nexus-workspace-two"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            manifest = write_bundle(graphs, out=output, cwd="/tmp/fallback-project")
            expected_keys = sorted(project_directory_name(item.workspace) for item in graphs)
            self.assertEqual(manifest["target_project_keys"], expected_keys)
            self.assertNotIn(project_directory_name("/tmp/fallback-project"), expected_keys)
            for session in manifest["target_sessions"]:
                graph_for_session = next(item for item in graphs if item.source_id == session["source_id"])
                self.assertIn(project_directory_name(graph_for_session.workspace), session["target_relative_path"])
                target = output / session["target_relative_path"]
                records = [json.loads(line) for line in target.read_text().splitlines()]
                self.assertEqual(records[0]["cwd"], str(Path(graph_for_session.workspace).resolve()))

    def test_project_slug_and_secret_scanner_do_not_return_secret_values(self) -> None:
        resolved = str(Path("/tmp/a.b_c").resolve())
        expected = re.sub(r"[^A-Za-z0-9]", "-", resolved)
        self.assertEqual(project_directory_name("/tmp/a.b_c"), expected)
        result = scan_secret_markers({"text": "sk-ant-" + "A" * 25})
        self.assertEqual(result, {"anthropic_api_key": 1})
        self.assertNotIn("A" * 25, json.dumps(result))


def _node(node_id: str, parent_id: str, child_ids: tuple[str, ...]):
    from nexus_memory.model import MessageNode

    return MessageNode(node_id, parent_id, child_ids, "assistant", "x", None, "x", {})


if __name__ == "__main__":
    unittest.main()

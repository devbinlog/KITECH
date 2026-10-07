"""Tests for sticky-note round-trip in scenario_converter.

Design Ref: §3 Data Model (StickyNote schema), §4 Converters
Plan SC: #9 (Sticky note YAML 보존)

Loads scenario_converter.py via importlib to avoid the unrelated relative-import
issue in services/__init__.py (sync_service import) that blocks normal
package import. The functions themselves are pure and self-contained.
"""

import importlib.util
from pathlib import Path

import pytest

# Load module directly (bypass services/__init__.py)
_SC_PATH = (
    Path(__file__).parent.parent.parent
    / "src"
    / "app"
    / "services"
    / "scenario_converter.py"
)
_spec = importlib.util.spec_from_file_location("sc_test_module", _SC_PATH)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


# ---------------------------------------------------------------------------
# Round-trip preservation
# ---------------------------------------------------------------------------


def test_sticky_round_trip_preserves_all_fields():
    """A scenario with notes survives YAML→n8n→YAML conversion."""
    src = {
        "name": "RT",
        "assets": [{"id": "A", "name": "AAA"}],
        "steps": [
            {
                "id": "s1",
                "name": "S1",
                "action": "{{acq.main}}/api/move",
                "params": {},
            }
        ],
        "notes": [
            {
                "x": 100,
                "y": 200,
                "w": 240,
                "h": 180,
                "text": "TODO: review",
                "color": "yellow",
            },
            {
                "x": 50,
                "y": 50,
                "w": 300,
                "h": 100,
                "text": "BLUE NOTE",
                "color": "blue",
            },
        ],
    }
    wf = sc.yaml_to_n8n_from_dict(src)
    rec = sc.n8n_to_yaml_from_dict(wf)
    assert rec.get("notes") == src["notes"]


def test_sticky_appears_as_correct_n8n_node_type():
    """Each note becomes a stickyNote n8n node with correct type+params."""
    src = {
        "name": "T",
        "assets": [],
        "steps": [{"id": "s1", "name": "S1", "action": "a", "params": {}}],
        "notes": [
            {
                "x": 1,
                "y": 2,
                "w": 3,
                "h": 4,
                "text": "hello",
                "color": "green",
            }
        ],
    }
    wf = sc.yaml_to_n8n_from_dict(src)
    sticky = [n for n in wf["nodes"] if n["type"] == sc.STICKY_TYPE]
    assert len(sticky) == 1
    s = sticky[0]
    assert s["position"] == [1, 2]
    assert s["parameters"]["width"] == 3
    assert s["parameters"]["height"] == 4
    assert s["parameters"]["content"] == "hello"
    assert s["parameters"]["color"] == sc.COLOR_NAME_TO_INT["green"]


@pytest.mark.parametrize("color", ["yellow", "blue", "pink", "green"])
def test_color_round_trip(color):
    """Each supported color survives the round trip."""
    src = {
        "name": "C",
        "assets": [],
        "steps": [{"id": "s1", "name": "S1", "action": "a", "params": {}}],
        "notes": [
            {"x": 0, "y": 0, "w": 240, "h": 180, "text": "x", "color": color}
        ],
    }
    rec = sc.n8n_to_yaml_from_dict(sc.yaml_to_n8n_from_dict(src))
    assert rec["notes"][0]["color"] == color


def test_unknown_color_defaults_to_yellow_on_recovery():
    """An unrecognized n8n color int recovers as 'yellow' (safe default)."""
    fake_node = {
        "id": "x",
        "name": "Sticky Note",
        "type": sc.STICKY_TYPE,
        "typeVersion": 1,
        "position": [0, 0],
        "parameters": {
            "content": "weird",
            "width": 240,
            "height": 180,
            "color": 99,  # not in our map
        },
    }
    parsed = sc.parse_sticky_node(fake_node)
    assert parsed["color"] == "yellow"


# ---------------------------------------------------------------------------
# Backward compatibility — no notes
# ---------------------------------------------------------------------------


def test_no_notes_key_omitted_on_recovery():
    """Scenario without notes preserves absence of `notes` key."""
    src = {
        "name": "NoNotes",
        "assets": [],
        "steps": [{"id": "s1", "name": "S1", "action": "a", "params": {}}],
    }
    rec = sc.n8n_to_yaml_from_dict(sc.yaml_to_n8n_from_dict(src))
    assert "notes" not in rec


def test_empty_notes_list_omitted_on_recovery():
    """Empty notes list also yields no `notes` key (clean YAML)."""
    src = {
        "name": "Empty",
        "assets": [],
        "steps": [{"id": "s1", "name": "S1", "action": "a", "params": {}}],
        "notes": [],
    }
    rec = sc.n8n_to_yaml_from_dict(sc.yaml_to_n8n_from_dict(src))
    assert "notes" not in rec

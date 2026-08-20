from pathlib import Path

from workforge.cli import _output_dir_for, _output_ref_for, _save_output


def test_output_dir_for_uses_input_stem_under_workspace_output() -> None:
    output_dir = _output_dir_for(
        Path("workspaces/sample-project"),
        Path("workspaces/sample-project/inbox/release-requirements.md"),
    )

    assert output_dir == Path("workspaces/sample-project/output/release-requirements")


def test_output_ref_for_uses_input_file_or_output_name() -> None:
    input_file = Path("inbox/release-requirements.md")

    assert _output_ref_for(input_file, "discovered") == input_file
    assert _output_ref_for(None, "discovered") == Path("discovered")


def test_save_output_writes_json_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    input_file = workspace / "inbox" / "requirements.md"
    payload = [{"title": "Fix UI"}]

    output_path = _save_output(workspace, input_file, "items.json", payload)

    assert output_path == workspace / "output" / "requirements" / "items.json"
    assert output_path.read_text() == '[\n  {\n    "title": "Fix UI"\n  }\n]\n'

from pathlib import Path

from workforge.cli import _output_dir_for, _save_output


def test_output_dir_for_uses_input_stem_under_workspace_output() -> None:
    output_dir = _output_dir_for(
        Path("workspaces/linkealo"),
        Path("workspaces/linkealo/inbox/shopify-feedback-app-review.md"),
    )

    assert output_dir == Path("workspaces/linkealo/output/shopify-feedback-app-review")


def test_save_output_writes_json_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    input_file = workspace / "inbox" / "requirements.md"
    payload = [{"title": "Fix UI"}]

    output_path = _save_output(workspace, input_file, "cards.json", payload)

    assert output_path == workspace / "output" / "requirements" / "cards.json"
    assert output_path.read_text() == '[\n  {\n    "title": "Fix UI"\n  }\n]\n'

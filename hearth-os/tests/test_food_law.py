from pathlib import Path

FORBIDDEN_UI = ("therapeutic", "anti-cancer", "cures", "unlock your potential")


def test_templates_have_no_medical_claims():
    root = Path(__file__).resolve().parents[1] / "app"
    blob = ""
    for path in list(root.joinpath("templates").glob("*.html")) + [
        root / "agents" / "prompts.py",
        root / "static" / "app.css",
    ]:
        blob += path.read_text(encoding="utf-8").lower()
    for word in FORBIDDEN_UI:
        assert word not in blob
    html = "\n".join(p.read_text(encoding="utf-8").lower() for p in root.joinpath("templates").glob("*.html"))
    assert "cancer" not in html
    assert "flu" not in html


def test_home_html_has_no_disease_words(logged_in, client):
    html = client.get("/").text.lower()
    assert "cancer" not in html
    assert "flu" not in html
    assert "estimate" in html

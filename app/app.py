"""Small Flask web app used to demonstrate the DevOps pipeline.

Interactive element: a "release notes" form. The page also shows the deployed
version (git commit SHA) and the EC2 instance serving the request, which makes
the rolling deployment and load balancing visible on screen.
"""
import os
import urllib.request
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

NOTES = []          # in-memory only: deliberately stateless (discussed in design)
MAX_NOTES = 50
MAX_LEN = 280
_instance_id = None


def get_version():
    """Version = commit SHA written at build time (VERSION file) or env var."""
    env = os.environ.get("APP_VERSION")
    if env:
        return env
    vfile = Path(__file__).with_name("VERSION")
    return vfile.read_text().strip() if vfile.exists() else "dev"


def get_instance_id():
    """Read the EC2 instance id via IMDSv2; fall back to 'local' off AWS."""
    global _instance_id
    if _instance_id:
        return _instance_id
    try:
        tok_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "300"},
        )
        token = urllib.request.urlopen(tok_req, timeout=0.5).read().decode()
        id_req = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
        )
        _instance_id = urllib.request.urlopen(id_req, timeout=0.5).read().decode()
    except Exception:
        _instance_id = "local"
    return _instance_id


PAGE = """
<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <title>DevOps Pipeline Demo</title>
  <style>
    body{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;
         padding:0 1rem;color:#222}
    .badge{display:inline-block;background:#0b5;color:#fff;padding:.2rem .6rem;
           border-radius:4px;margin-right:.4rem}
    li{margin:.3rem 0}
  </style>
</head>
<body>
  <h1>Release board</h1>
  <p><span class="badge">version {{ version }}</span>
     <span class="badge" style="background:#06c">served by {{ instance }}</span></p>
  <form method="post" action="{{ url_for('add_note') }}">
    <input name="note" maxlength="280" placeholder="Add a release note" required>
    <button type="submit">Add</button>
  </form>
  <ul>{% for n in notes %}<li>{{ n }}</li>{% else %}<li>No notes yet.</li>{% endfor %}</ul>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        PAGE, version=get_version(), instance=get_instance_id(), notes=reversed(NOTES)
    )


@app.post("/notes")
def add_note():
    note = request.form.get("note", "").strip()[:MAX_LEN]
    if not note:
        return "Note must not be empty", 400
    NOTES.append(note)
    del NOTES[:-MAX_NOTES]
    return redirect(url_for("index"))


@app.get("/health")
def health():
    return jsonify(status="ok", version=get_version(), instance=get_instance_id())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

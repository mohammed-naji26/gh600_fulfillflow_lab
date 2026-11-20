"""Compare persisted task state with the current HEAD and fail on stale state."""
import json
import subprocess
import sys
from pathlib import Path
path = Path(sys.argv[1] if len(sys.argv)>1 else "docs/templates/task_state.example.json")
state = json.loads(path.read_text())
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
print(f"State SHA: {state['commit_sha']} | HEAD: {sha}")
if state["commit_sha"] != sha:
    raise SystemExit("STALE STATE: re-evaluate latest commit before continuing")
print("State is current")

"""Atomic STATUS.json writer for Opus B (verification_v11)."""
import json, os, sys, datetime, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "STATUS.json")
BASE = {
    "agent": "Opus B (verification: grid/timestep/perturbation/parameter)",
    "resolved_model": "claude-opus-5-5",
    "resolved_model_evidence": "model_revision_plan/20261030_opus_campaign/verification_stream.jsonl init event model=claude-opus-5-5",
    "report_path": "model_revisions/20261030_verification_v11/VERIFICATION_REPORT.md",
}
def update(**kw):
    cur = {}
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            cur = json.load(f)
    cur.update(BASE); cur.update(kw)
    cur["updated_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    fd, tmp = tempfile.mkstemp(dir=ROOT, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cur, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return cur
if __name__ == "__main__":
    kw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(update(**kw), indent=2, ensure_ascii=False))

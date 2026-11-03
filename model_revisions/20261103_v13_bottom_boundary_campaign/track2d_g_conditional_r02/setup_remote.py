"""Create an isolated conditional 2D G production root from frozen track2d."""
from pathlib import Path
import hashlib
import json
import shutil
import socket

assert socket.gethostname() == "frodo"
R = Path(__file__).resolve().parent
SOURCE = R.parent / "track2d"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name in ["inputs", "source", "build_sal"]:
    source = SOURCE / name
    target = R / name
    assert source.exists() and not target.exists(), (source, target)
    shutil.copytree(source, target, copy_function=shutil.copy2)

for name in ["runner.py", "analyze.py", "input_manifest.json"]:
    shutil.copy2(SOURCE / name, R / name)

original_manifest = json.loads((SOURCE / "build_sal/build_manifest.json").read_text())
copied_manifest = json.loads((R / "build_sal/build_manifest.json").read_text())
assert copied_manifest == original_manifest
assert sha(R / "build_sal/heterogeneity_revised") == copied_manifest["binary_sha256"]
for relative, digest in copied_manifest["source_sha256"].items():
    assert sha(R / relative) == digest, relative
for name, digest in json.loads((R / "input_manifest.json").read_text()).items():
    assert sha(R / "inputs" / name) == digest, name

(R / "raw").mkdir()
(R / "results").mkdir()
(R / "status").mkdir()
(R / "provenance").mkdir()
(R / "provenance/setup_receipt.json").write_text(
    json.dumps(
        dict(
            state="passed",
            source_root=str(SOURCE),
            native_binary_sha256=copied_manifest["binary_sha256"],
            frozen_inputs=len(json.loads((R / "input_manifest.json").read_text())),
            change="orchestration isolation only; production physics and numerics unchanged",
        ),
        indent=2,
    )
)
print("Conditional 2D G root verified", flush=True)


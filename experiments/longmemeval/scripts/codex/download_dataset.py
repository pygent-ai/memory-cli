import argparse
import json
import urllib.request
from pathlib import Path


FILES = {
    "oracle": "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_oracle.json",
    "s": "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json",
    "m": "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_m_cleaned.json",
}


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return {"path": str(path), "status": "exists", "bytes": path.stat().st_size}

    with urllib.request.urlopen(url) as response:
        with path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)

    return {"path": str(path), "status": "downloaded", "bytes": path.stat().st_size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=FILES, default="oracle")
    parser.add_argument("--out-dir", default="datasets/longmemeval/raw")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    name = {
        "oracle": "longmemeval_oracle.json",
        "s": "longmemeval_s_cleaned.json",
        "m": "longmemeval_m_cleaned.json",
    }[args.dataset]
    result = download(FILES[args.dataset], out_dir / name)

    manifest = out_dir / "manifest.json"
    manifest_data = {}
    if manifest.exists():
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_data[args.dataset] = {
        "url": FILES[args.dataset],
        "file": name,
        "bytes": result["bytes"],
    }
    manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Publish a Smol Town JSONL agent trace as a Hugging Face dataset."""
import argparse
import io
import json
import os
from pathlib import Path

from huggingface_hub import HfApi


DATASET_CARD = """---
license: apache-2.0
pretty_name: Smol Town Agent Traces
---

# Smol Town Agent Traces

Agent-generation traces exported from
[Smol Town](https://github.com/siddhant-rajhans/smol-town).

Each JSONL row contains:

- `tick`: simulation tick
- `speaker`: villager name
- `role`: villager role
- `model`: generating model
- `context`: recent feed lines supplied to the model
- `system`: complete agent system prompt
- `output`: cleaned generated line
- `ts`: ISO-8601 UTC timestamp
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Publish a Smol Town agent-trace JSONL file to the Hugging Face Hub.")
    parser.add_argument("--repo-id", required=True, help="Dataset repo, for example user/smol-town-traces")
    parser.add_argument("--file", required=True, type=Path, help="Trace JSONL file to upload")
    return parser.parse_args()


def validate_jsonl(path):
    count = 0
    with path.open(encoding="utf-8") as trace_file:
        for line_number, line in enumerate(trace_file, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            count += 1
    return count


def main():
    args = parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Trace file not found: {args.file}")

    token = os.getenv("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN must be set to publish a dataset")

    try:
        row_count = validate_jsonl(args.file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"Invalid trace JSONL: {exc}") from exc

    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo_id, repo_type="dataset", exist_ok=True)
    api.upload_file(
        path_or_fileobj=str(args.file),
        path_in_repo=f"data/{args.file.name}",
        repo_id=args.repo_id,
        repo_type="dataset",
        commit_message="Upload Smol Town agent traces",
    )
    api.upload_file(
        path_or_fileobj=io.BytesIO(DATASET_CARD.encode("utf-8")),
        path_in_repo="README.md",
        repo_id=args.repo_id,
        repo_type="dataset",
        commit_message="Add agent-trace dataset card",
    )
    print(f"Published {row_count} traces to https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()

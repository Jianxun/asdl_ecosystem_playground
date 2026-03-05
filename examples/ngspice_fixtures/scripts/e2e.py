#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class StageResult:
    name: str
    ok: bool
    command: list[str] | None = None
    details: str | None = None


def _run_cmd(stage: str, cmd: list[str], cwd: Path) -> StageResult:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode == 0:
        return StageResult(name=stage, ok=True, command=cmd)

    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    tail = stderr or stdout or "(no output)"
    if len(tail) > 600:
        tail = tail[-600:]
    return StageResult(
        name=stage,
        ok=False,
        command=cmd,
        details=f"exit={proc.returncode}; tail={tail}",
    )


def _run_first_success(stage: str, commands: list[list[str]], cwd: Path) -> StageResult:
    last_fail: StageResult | None = None
    for cmd in commands:
        rs = _run_cmd(stage, cmd, cwd)
        if rs.ok:
            return rs
        last_fail = rs
    assert last_fail is not None
    return last_fail


def _find_h5_files(hdf5_dir: Path) -> list[Path]:
    if not hdf5_dir.exists():
        return []
    return sorted([*hdf5_dir.glob("*.h5"), *hdf5_dir.glob("*.hdf5")])


def _query_smoke(cwd: Path, hdf5_dir: Path, query_script: Path) -> StageResult:
    h5_files = _find_h5_files(hdf5_dir)
    if not h5_files:
        return StageResult(
            name="query-smoke",
            ok=False,
            details=f"no HDF5 artifacts found in {hdf5_dir}",
        )

    for fp in h5_files:
        rs = _run_first_success(
            "query-smoke",
            commands=[
                [sys.executable, str(query_script), str(fp), "summary"],
            ],
            cwd=cwd,
        )
        if not rs.ok:
            rs.details = f"file={fp}; {rs.details}"
            return rs

        rs = _run_first_success(
            "query-smoke",
            commands=[
                [sys.executable, str(query_script), str(fp), "list-signals"],
            ],
            cwd=cwd,
        )
        if not rs.ok:
            rs.details = f"file={fp}; {rs.details}"
            return rs

    return StageResult(name="query-smoke", ok=True, details=f"checked {len(h5_files)} file(s)")


def _gather_artifacts(raw_dir: Path, hdf5_dir: Path, analysis_dir: Path) -> dict[str, list[str]]:
    raw = sorted(str(p) for p in raw_dir.rglob("*.raw")) if raw_dir.exists() else []
    h5 = sorted(str(p) for p in _find_h5_files(hdf5_dir))
    analysis = sorted(str(p) for p in analysis_dir.rglob("*.json")) if analysis_dir.exists() else []
    return {
        "raw": raw,
        "hdf5": h5,
        "analysis": analysis,
    }


def _require_paths(paths: Iterable[Path]) -> list[str]:
    missing: list[str] = []
    for p in paths:
        if not p.exists():
            missing.append(str(p))
    return missing


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run end-to-end fixture->normalize->query->analyze regression.")
    p.add_argument("--repo-root", default=".", help="Repository root containing scripts/ and tools/")
    p.add_argument("--raw-dir", default="outputs/raw", help="RAW artifact directory")
    p.add_argument("--hdf5-dir", default="outputs/hdf5", help="HDF5 artifact directory")
    p.add_argument("--analysis-dir", default="outputs/analysis", help="Analysis artifact directory")
    p.add_argument("--json", action="store_true", help="Emit machine-readable final summary JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()

    repo_root = Path(args.repo_root).resolve()
    raw_dir = (repo_root / args.raw_dir).resolve()
    hdf5_dir = (repo_root / args.hdf5_dir).resolve()
    analysis_dir = (repo_root / args.analysis_dir).resolve()

    fixture_runner = repo_root / "scripts" / "run_fixtures.py"
    normalizer = repo_root / "tools" / "normalize_raw.py"
    query_script = repo_root / "tools" / "h5_query.py"
    analyzer_adapter = repo_root / "tools" / "run_analyzers.py"

    missing = _require_paths([fixture_runner, normalizer, query_script, analyzer_adapter])
    if missing:
        msg = {
            "status": "failed",
            "failed_stage": "preflight",
            "error": "missing required scripts",
            "missing": missing,
        }
        if args.json:
            print(json.dumps(msg, indent=2))
        else:
            print("❌ e2e failed at stage=preflight")
            print("Missing required scripts:")
            for m in missing:
                print(f"- {m}")
        return 2

    # Ensure output directories exist (stages may rely on this).
    raw_dir.mkdir(parents=True, exist_ok=True)
    hdf5_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    stages: list[StageResult] = []

    stages.append(
        _run_first_success(
            "fixtures",
            commands=[
                [sys.executable, str(fixture_runner), "--out-dir", str(raw_dir)],
                [sys.executable, str(fixture_runner)],
            ],
            cwd=repo_root,
        )
    )
    if not stages[-1].ok:
        return _finish(args.json, stages, raw_dir, hdf5_dir, analysis_dir)

    raw_files = sorted(raw_dir.rglob("*.raw"))
    if not raw_files:
        stages.append(StageResult(name="normalize", ok=False, details=f"no RAW files found in {raw_dir}"))
        return _finish(args.json, stages, raw_dir, hdf5_dir, analysis_dir)

    for raw_fp in raw_files:
        case_id = raw_fp.parent.name
        out_fp = hdf5_dir / f"{case_id}.h5"
        rs = _run_first_success(
            "normalize",
            commands=[
                [
                    sys.executable,
                    str(normalizer),
                    "--input",
                    str(raw_fp),
                    "--output",
                    str(out_fp),
                    "--case-id",
                    case_id,
                ],
                [
                    sys.executable,
                    str(normalizer),
                    "--raw",
                    str(raw_fp),
                    "--hdf5",
                    str(out_fp),
                    "--case-id",
                    case_id,
                ],
            ],
            cwd=repo_root,
        )
        if not rs.ok:
            rs.details = f"raw={raw_fp}; {rs.details}"
            stages.append(rs)
            return _finish(args.json, stages, raw_dir, hdf5_dir, analysis_dir)
    stages.append(StageResult(name="normalize", ok=True, details=f"converted {len(raw_files)} RAW file(s)"))

    stages.append(_query_smoke(repo_root, hdf5_dir, query_script))
    if not stages[-1].ok:
        return _finish(args.json, stages, raw_dir, hdf5_dir, analysis_dir)

    stages.append(
        _run_first_success(
            "analyzer-adapter",
            commands=[
                [sys.executable, str(analyzer_adapter), "--input", str(hdf5_dir), "--output-dir", str(analysis_dir)],
            ],
            cwd=repo_root,
        )
    )

    return _finish(args.json, stages, raw_dir, hdf5_dir, analysis_dir)


def _finish(json_mode: bool, stages: list[StageResult], raw_dir: Path, hdf5_dir: Path, analysis_dir: Path) -> int:
    failed = next((s for s in stages if not s.ok), None)
    artifacts = _gather_artifacts(raw_dir, hdf5_dir, analysis_dir)

    payload = {
        "status": "failed" if failed else "ok",
        "failed_stage": failed.name if failed else None,
        "stages": [
            {
                "name": s.name,
                "ok": s.ok,
                "command": s.command,
                "details": s.details,
            }
            for s in stages
        ],
        "artifacts": artifacts,
    }

    if json_mode:
        print(json.dumps(payload, indent=2))
    else:
        if failed:
            print(f"❌ e2e failed at stage={failed.name}")
            if failed.details:
                print(f"   {failed.details}")
        else:
            print("✅ e2e succeeded")

        print("Artifacts:")
        print(f"- RAW:      {raw_dir}")
        print(f"- HDF5:     {hdf5_dir}")
        print(f"- Analysis: {analysis_dir}")

        if failed:
            print("Stage summary:")
            for s in stages:
                flag = "ok" if s.ok else "fail"
                print(f"- {s.name}: {flag}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

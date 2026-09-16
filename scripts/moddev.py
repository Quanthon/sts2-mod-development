#!/usr/bin/env python3
"""STS2 design implementation tools. All paths are relative to --config project_root."""
from __future__ import annotations
import argparse
import json
import sys
from common import Project, SCHEMAS

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create design templates/config in a project; never overwrite")
    init.add_argument("--project", required=True)
    init.add_argument("--profile", choices=["common", "character"], default="common")
    for name in ("doctor", "add-content", "diff", "record", "accept", "placeholder", "sync-art", "icons"):
        q = sub.add_parser(name)
        q.add_argument("--config", required=True)
        if name in ("diff", "record", "accept"):
            q.add_argument("--kind", choices=list(SCHEMAS), required=name != "diff")
            q.add_argument("--key", action="append", required=name == "record")
        if name == "record":
            q.add_argument("--artifact", action="append", required=True)
            q.add_argument("--check", action="append", required=True)
            q.add_argument("--behavior", choices=["passed", "reused", "skipped"], required=True)
            q.add_argument("--reason", default="")
            q.add_argument("--implementation-id")
        if name == "placeholder":
            q.add_argument("--key", required=True)
            q.add_argument("--name", default="")
            q.add_argument("--type", default="技能")
            q.add_argument("--refresh", action="store_true")
            q.add_argument("--font", help="Font file for placeholder labels; relative to project or absolute")
        if name == "sync-art":
            q.add_argument("--kind", choices=["cards", "powers", "relics"])
            q.add_argument("--apply", action="store_true")
        if name == "icons":
            q.add_argument("--key", action="append")
            q.add_argument("--apply", action="store_true")
            q.add_argument("--overwrite", action="store_true")
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "init":
        from templates import init_project
        result = init_project(args.project, args.profile)
    else:
        project = Project(args.config)
        if args.command == "add-content":
            from templates import add_content
            result = add_content(project)
        elif args.command == "doctor":
            from doctor import doctor
            result = doctor(project)
        elif args.command == "diff":
            from design import differences
            result, _ = differences(project, [args.kind] if args.kind else None, args.key)
        elif args.command == "record":
            from design import record
            if len(args.key) != 1:
                raise ValueError("record takes one --key per verification record")
            result = record(project, args.kind, args.key[0], args.artifact, args.check,
                            args.behavior, args.reason, args.implementation_id)
        elif args.command == "accept":
            from design import accept
            result = accept(project, args.kind, args.key)
        elif args.command == "placeholder":
            from art import placeholder
            result = placeholder(project, args.key, args.name, args.type, args.refresh, args.font)
        elif args.command == "sync-art":
            from art import sync
            result = sync(project, args.apply, args.kind)
        elif args.command == "icons":
            from art import icons
            result = icons(project, args.apply, args.key, args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get("issues") or result.get("missing") else 0

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, ImportError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


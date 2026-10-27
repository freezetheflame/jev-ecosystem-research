"""Run exported static benchmarks with the existing Jev workspace and monitor."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True,
                        help='Existing jev-skill-security workspace, with monitor and benchmark dependencies')
    parser.add_argument('mode', choices=['check', 'test', 'compare', 'repair', 'resources'])
    args, rest = parser.parse_known_args()
    workspace = args.workspace.resolve()
    manifest = json.loads(Path(__file__).with_name('source-manifest.json').read_text(encoding='utf-8'))
    checks = []
    for entry in manifest['external_dependencies']:
        path = workspace / entry['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        checks.append({'path': entry['path'], 'present': actual is not None,
                       'matches_export_environment': actual == entry['sha256'], 'actual_sha256': actual})
    if args.mode == 'check':
        print(json.dumps(checks, indent=2))
        return 0 if all(r['present'] and r['matches_export_environment'] for r in checks) else 1
    if not all(r['present'] for r in checks):
        parser.error('Missing workspace dependencies; use check and prepare the source workspace first')
    if not all(r['matches_export_environment'] for r in checks):
        parser.error('Workspace differs from exported dependency snapshot; validate and version a new source manifest before running')
    os.environ['JEV_WORKSPACE_ROOT'] = str(workspace)
    sys.path.insert(0, str(workspace))
    # UTF-8 affects console rendering, not saved request bytes or model parameters.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    if args.mode == 'test':
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).with_name('tests')))
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    names = {'compare': 'type_compare', 'repair': 'type_compare_repair', 'resources': 'type_compare_resources'}
    module = importlib.import_module('framework.' + names[args.mode])
    sys.argv = [str(Path(module.__file__))] + rest
    # Exported scripts interpret relative output paths from the source workspace.
    os.chdir(workspace)
    if args.mode in ('compare', 'repair'):
        from jev_skill.monitor import monitored_run
        # The original post_json already has @monitored_call. Never add another.
        # Persist this invocation's dependency check with telemetry, not in gold data.
        from jev_skill.monitor import annotate_run
        @monitored_run
        def invoke():
            annotate_run(adapter='framework.' + names[args.mode], workspace_dependencies=checks,
                         exported_adapter_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
            module.main()
        invoke()
    else:
        module.main()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

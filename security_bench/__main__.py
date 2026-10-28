import argparse
import json
import sys
from .common import read
from .config import inspect


def main():
    p = argparse.ArgumentParser(description='Four-benchmark safety-role study; no silent model calls in doctor/plan/report.')
    p.add_argument('command', choices=['doctor', 'plan', 'run', 'report', 'check-environment', 'inspect-inputs', 'inspect-models'])
    p.add_argument('--config', default='configs/security-bench.template.json')
    p.add_argument('--run-dir')
    p.add_argument('--out-dir', help='New directory for offline inspect-inputs artifacts')
    p.add_argument('--split', action='append', choices=['validation','test_public'], help='inspect-inputs only; explicit source split override')
    p.add_argument('--resume', action='store_true')
    p.add_argument('--benchmark-version', help='Explicit AgentDojo version for offline check-environment only')
    p.add_argument('--skip-key-check', action='store_true', help='doctor only; never bypass live credential checks')
    args = p.parse_args()
    try:
        config = read(args.config)
        if args.command == 'inspect-models':
            if not args.out_dir:
                p.error('--out-dir is required for inspect-models')
            from .model_preview import preview
            print(json.dumps(preview(config, args.out_dir), ensure_ascii=False, indent=2))
            return 0
        if args.command == 'inspect-inputs':
            if not args.out_dir:
                p.error('--out-dir is required for inspect-inputs')
            from .agentharm import inspect_inputs
            print(json.dumps(inspect_inputs(config, args.out_dir, args.split), ensure_ascii=False, indent=2))
            return 0
        if args.command == 'doctor':
            result = inspect(config, check_keys=not args.skip_key_check)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['status'] == 'ready' else 2
        if args.command == 'check-environment':
            if 'agentdojo' not in config['datasets']:
                raise ValueError('Current selection has no AgentDojo; use its preserved legacy config for environment diagnostics')
            if args.benchmark_version:
                config['datasets']['agentdojo']['benchmark_version'] = args.benchmark_version
            if not config['datasets']['agentdojo'].get('benchmark_version'):
                raise ValueError('Pass --benchmark-version explicitly for offline environment inspection')
            from .dojo import suites
            registry = suites(config)
            result = {'status': 'official_environment_loaded_not_model_experiment', 'network_calls': 0, 'suites': {}}
            for name in config['datasets']['agentdojo']['suites']:
                suite = registry[name]
                env = suite.load_and_inject_default_environment({})
                result['suites'][name] = {'user_tasks': len(suite.user_tasks),
                    'injection_tasks': len(suite.injection_tasks), 'tools': len(suite.tools),
                    'environment_type': type(env).__name__}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not args.run_dir:
            p.error('--run-dir is required for plan, run and report')
        if args.command == 'report':
            from .report import report
            result = report(args.run_dir)
        else:
            from .runner import plan, execute
            result = plan(config, args.run_dir) if args.command == 'plan' else execute(config, args.run_dir, args.resume)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        # Config may contain secrets if incorrectly edited: never print its values.
        # Our own ValueErrors are deliberately descriptive without credential values.
        print(json.dumps({'status': 'failed', 'error_type': type(exc).__name__,
                          'reason': str(exc) if isinstance(exc, (ValueError, FileExistsError)) else 'See local configuration/dependencies; no exception payload printed.'}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())

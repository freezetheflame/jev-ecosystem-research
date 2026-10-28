"""Save actual offline engineering checks, never synthetic benchmark measurements."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = [
        ('unit-tests', ['-m', 'unittest', 'discover', '-s', 'security_bench/tests', '-v'], 0),
        ('environment', ['-m', 'security_bench', 'check-environment', '--config', 'configs/security-bench-agentdojo.template.json', '--benchmark-version', 'v1.2.2'], 0),
        ('dependency-check', ['-m', 'pip', 'check'], 0),
        ('template-preflight', ['-m', 'security_bench', 'doctor', '--skip-key-check'], 2),
        ('agentharm-preflight', ['-m', 'security_bench', 'doctor', '--config', 'configs/agentharm-a1.template.json', '--skip-key-check'], 2),
        ('all-model-preflight', ['-m', 'security_bench', 'doctor', '--config', 'configs/security-bench-all-models.template.json', '--skip-key-check'], 2),
        ('all-model-request-preview', ['-m', 'security_bench', 'inspect-models', '--config', 'configs/agentharm-all-models.template.json', '--out-dir', str(out / 'request-previews')], 0),
    ]
    results = []
    for name, arguments, expected in commands:
        print('Offline check: ' + name, flush=True)
        process = subprocess.run([sys.executable, *arguments], cwd=ROOT, capture_output=True, encoding='utf-8')
        (out / (name + '.stdout.txt')).write_text(process.stdout, encoding='utf-8')
        (out / (name + '.stderr.txt')).write_text(process.stderr, encoding='utf-8')
        results.append({'name': name, 'command': [sys.executable, *arguments], 'exit_code': process.returncode,
                        'expected_exit_code': expected, 'passed': process.returncode == expected})
    sys.path.insert(0, str(ROOT))
    from security_bench.common import sources, file_hash
    from security_bench.models import load_monitor
    from security_bench.common import read
    module = load_monitor(read(ROOT / 'configs/security-bench.template.json'))
    verification = {'record_kind': 'offline_engineering_verification_not_experiment',
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'passed' if all(x['passed'] for x in results) else 'failed',
        'network_model_calls': 0, 'benchmark_performance_results': 'not_run',
        'fixture_policy': 'Synthetic responses/rates in unit tests only; temporary directories removed.',
        'checks': results, 'source_hashes': sources(), 'monitor_sha256': file_hash(module.__file__),
        'dependency_lock_sha256': file_hash(ROOT / 'requirements/security-bench-py312.lock.txt')}
    (out / 'verification.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(verification['status'], flush=True)
    return 0 if verification['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())

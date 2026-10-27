import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from framework import run


class RunnerTests(unittest.TestCase):
    def test_relative_outputs_run_from_source_workspace_without_api(self):
        workspace = Path(os.environ['JEV_WORKSPACE_ROOT'])
        before = Path.cwd()
        observed = []
        module = SimpleNamespace(__file__=__file__, main=lambda: observed.append(Path.cwd()))
        try:
            with patch('sys.argv', ['run', '--workspace', str(workspace), 'resources']), patch.object(run.importlib, 'import_module', return_value=module):
                self.assertEqual(run.main(), 0)
        finally:
            os.chdir(before)
        self.assertEqual(observed, [workspace])


if __name__ == '__main__':
    unittest.main()

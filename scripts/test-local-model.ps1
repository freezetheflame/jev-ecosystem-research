param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('plumb', 'decider', 'h2o')]
    [string]$Model,
    [switch]$Graphs
)

$taskRoot = Split-Path -Parent $PSScriptRoot
$taskWslRoot = (wsl -d Ubuntu -- wslpath -a ($taskRoot.Replace('\', '/'))).Trim()
if (-not $taskWslRoot) { throw 'Could not resolve the workspace path in WSL.' }
$taskPython = '/home/hectum/.cache/jev-research-env/bin/python'
$taskArguments = @('-d', 'Ubuntu', '--', $taskPython, '-u', "$taskWslRoot/scripts/local_model_smoke.py", $Model)
if ($Graphs) { $taskArguments += '--graphs' }
& wsl @taskArguments
exit $LASTEXITCODE

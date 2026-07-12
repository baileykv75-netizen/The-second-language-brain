param(
    [Parameter(Mandatory = $true)]
    [string]$SessionFile
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$PythonCandidates = @(
    "python",
    "py",
    "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$Python = $null
foreach ($Candidate in $PythonCandidates) {
    try {
        $Command = Get-Command $Candidate -ErrorAction Stop
        $Python = $Command.Source
        break
    } catch {
        if (Test-Path -LiteralPath $Candidate) {
            $Python = $Candidate
            break
        }
    }
}

if (-not $Python) {
    throw "Python was not found. Install Python or run this project from Codex with the bundled runtime."
}

$ProcessScript = Join-Path $RepoRoot "scripts\process_session.py"
$IndexScript = Join-Path $RepoRoot "scripts\build_indexes.py"
$ReviewScript = Join-Path $RepoRoot "scripts\build_review.py"

& $Python $ProcessScript $SessionFile
& $Python $IndexScript
& $Python $ReviewScript

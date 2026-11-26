# Build standalone Windows GUI NexusMemory.exe using PyInstaller
$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

python -m pip install --upgrade pip pyinstaller
python -m PyInstaller --clean --noconfirm packaging/windows/nexus_memory.spec

Write-Host "Built Windows GUI binary at: $RepoRoot\dist\NexusMemory.exe"
& "$RepoRoot\dist\NexusMemory.exe" --self-test
& "$RepoRoot\dist\NexusMemory.exe" --cli matrix --from codex-cli --to claude-code

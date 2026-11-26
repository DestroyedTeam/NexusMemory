# Build standalone Windows GUI NexusMemory.exe using PyInstaller
$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

python -m pip install --upgrade pip pyinstaller
python -m PyInstaller --clean --noconfirm packaging/windows/nexus_memory.spec

Write-Host "Built Windows GUI binary at: $RepoRoot\dist\NexusMemory.exe"
$SelfTestOut = Join-Path $env:TEMP "nexus_selftest.json"
$MatrixOut = Join-Path $env:TEMP "nexus_matrix.json"
& "$RepoRoot\dist\NexusMemory.exe" --self-test --out-file $SelfTestOut
if ($LASTEXITCODE -ne 0) { throw "NexusMemory.exe --self-test failed" }
Get-Content $SelfTestOut
& "$RepoRoot\dist\NexusMemory.exe" --cli matrix --from codex-cli --to claude-code --out-file $MatrixOut
if ($LASTEXITCODE -ne 0) { throw "NexusMemory.exe --cli matrix failed" }
Get-Content $MatrixOut

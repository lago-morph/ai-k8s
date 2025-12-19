# PowerShell script to run prototype tests in mk8-test WSL instance
# Usage: .\run-tests-wsl.ps1 [test-file]

param(
    [string]$TestFile = ""
)

$WSL_INSTANCE = "mk8-test"
$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent
$WSL_PROJECT_ROOT = $PROJECT_ROOT -replace '\\', '/' -replace 'C:', '/mnt/c'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "mk8 Prototype Test Runner (WSL)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if WSL instance exists
$wslList = wsl --list --quiet
if ($wslList -notcontains $WSL_INSTANCE) {
    Write-Host "ERROR: WSL instance '$WSL_INSTANCE' not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available WSL instances:" -ForegroundColor Yellow
    wsl --list --verbose
    Write-Host ""
    Write-Host "To create the mk8-test instance, run:" -ForegroundColor Yellow
    Write-Host "  wsl --install -d Ubuntu-24.04 --name mk8-test" -ForegroundColor White
    Write-Host ""
    Write-Host "Then set it up with:" -ForegroundColor Yellow
    Write-Host "  wsl -d mk8-test --cd $WSL_PROJECT_ROOT bash prototype/setup-wsl-test-env.sh" -ForegroundColor White
    exit 1
}

Write-Host "✅ Using WSL instance: $WSL_INSTANCE" -ForegroundColor Green
Write-Host "📁 Project root: $PROJECT_ROOT" -ForegroundColor Gray
Write-Host "📁 WSL path: $WSL_PROJECT_ROOT" -ForegroundColor Gray
Write-Host ""

# Check if BATS is installed
Write-Host "🔍 Checking BATS installation..." -ForegroundColor Yellow
$batsCheck = wsl -d $WSL_INSTANCE bash -c "command -v bats"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: BATS not installed in $WSL_INSTANCE" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run the setup script:" -ForegroundColor Yellow
    Write-Host "  wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bash prototype/setup-wsl-test-env.sh" -ForegroundColor White
    exit 1
}

$batsVersion = wsl -d $WSL_INSTANCE bats --version
Write-Host "✅ BATS installed: $batsVersion" -ForegroundColor Green
Write-Host ""

# Run tests
if ($TestFile) {
    # Run specific test file
    $testPath = Join-Path $PROJECT_ROOT "prototype\tests\unit\$TestFile"
    if (-not (Test-Path $testPath)) {
        Write-Host "ERROR: Test file not found: $testPath" -ForegroundColor Red
        exit 1
    }
    
    $wslTestPath = "$WSL_PROJECT_ROOT/prototype/tests/unit/$TestFile"
    Write-Host "🧪 Running test file: $TestFile" -ForegroundColor Cyan
    Write-Host ""
    
    wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bats "prototype/tests/unit/$TestFile"
} else {
    # Run all tests
    Write-Host "🧪 Running all prototype tests..." -ForegroundColor Cyan
    Write-Host ""
    
    wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bats prototype/tests/unit/
}

$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ All tests passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ Tests failed with exit code: $exitCode" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

exit $exitCode

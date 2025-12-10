# Universal PowerShell test runner for Windows
# Automatically uses WSL for bash testing with credential isolation
#
# Usage:
#   .\scripts\run-tests.ps1 [test-file]
#   .\scripts\run-tests.ps1 -Shellcheck
#   .\scripts\run-tests.ps1 -Setup

param(
    [string]$TestFile = "",
    [switch]$Shellcheck = $false,
    [switch]$Setup = $false,
    [switch]$Help = $false
)

# Load configuration
$CONFIG_FILE = Join-Path (Split-Path $PSScriptRoot -Parent) ".test-config.json"

if (-not (Test-Path $CONFIG_FILE)) {
    Write-Host "ERROR: Configuration file not found: $CONFIG_FILE" -ForegroundColor Red
    exit 1
}

$config = Get-Content $CONFIG_FILE | ConvertFrom-Json
$WSL_INSTANCE = $config.wsl.instanceName
$WSL_DISTRO = $config.wsl.distribution
$SETUP_SCRIPT = $config.wsl.setupScript
$TEST_FRAMEWORK = $config.testing.framework
$TEST_DIR = $config.testing.testDirectory

$PROJECT_ROOT = Split-Path $PSScriptRoot -Parent
# Convert Windows path to WSL path (C:\path -> /mnt/c/path)
$driveLetter = $PROJECT_ROOT.Substring(0,1).ToLower()
$pathWithoutDrive = $PROJECT_ROOT.Substring(2) -replace '\\', '/'
$WSL_PROJECT_ROOT = "/mnt/$driveLetter$pathWithoutDrive"

function Show-Usage {
    Write-Host @"
Universal Test Runner (Windows)

USAGE:
    .\scripts\run-tests.ps1 [options] [test-file]

OPTIONS:
    -Shellcheck         Run shellcheck on bash scripts
    -Setup              Set up WSL testing environment
    -Help               Show this help message

ARGUMENTS:
    test-file           Optional: specific test file to run (e.g., test_crossplane.bats)

EXAMPLES:
    # Run all tests
    .\scripts\run-tests.ps1

    # Run specific test
    .\scripts\run-tests.ps1 test_crossplane.bats

    # Run shellcheck
    .\scripts\run-tests.ps1 -Shellcheck

    # Set up WSL instance
    .\scripts\run-tests.ps1 -Setup

CONFIGURATION:
    WSL Instance: $WSL_INSTANCE
    Distribution: $WSL_DISTRO
    Test Directory: $TEST_DIR

    Edit .test-config.json to customize settings
"@
}

function Test-WSLInstance {
    $wslList = wsl --list --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: WSL not available" -ForegroundColor Red
        Write-Host "Install WSL with: wsl --install" -ForegroundColor Yellow
        return $false
    }
    
    if ($wslList -notcontains $WSL_INSTANCE) {
        Write-Host "ERROR: WSL instance '$WSL_INSTANCE' not found" -ForegroundColor Red
        Write-Host ""
        Write-Host "Available WSL instances:" -ForegroundColor Yellow
        wsl --list --verbose
        Write-Host ""
        Write-Host "To create the testing instance, run:" -ForegroundColor Yellow
        Write-Host "  .\scripts\run-tests.ps1 -Setup" -ForegroundColor White
        return $false
    }
    
    return $true
}

function Setup-WSLInstance {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "WSL Testing Environment Setup" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if instance already exists
    $wslList = wsl --list --quiet 2>$null
    if ($wslList -contains $WSL_INSTANCE) {
        Write-Host "WSL instance '$WSL_INSTANCE' already exists" -ForegroundColor Yellow
        $response = Read-Host "Do you want to reinstall? This will DELETE the existing instance (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Host "Setup cancelled" -ForegroundColor Yellow
            exit 0
        }
        
        Write-Host "Unregistering existing instance..." -ForegroundColor Yellow
        wsl --unregister $WSL_INSTANCE
    }
    
    # Install new instance
    Write-Host "Installing WSL distribution: $WSL_DISTRO" -ForegroundColor Cyan
    Write-Host "Instance name: $WSL_INSTANCE" -ForegroundColor Cyan
    Write-Host ""
    
    # Try with --name flag first
    Write-Host "Attempting: wsl --install -d $WSL_DISTRO --name $WSL_INSTANCE" -ForegroundColor Gray
    wsl --install -d $WSL_DISTRO --name $WSL_INSTANCE 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Note: --name flag not supported, installing without it" -ForegroundColor Yellow
        wsl --install -d $WSL_DISTRO
        Write-Host ""
        Write-Host "IMPORTANT: Use 'wsl -d $WSL_DISTRO' to access this instance" -ForegroundColor Yellow
        $WSL_INSTANCE = $WSL_DISTRO
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "WSL instance created successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Complete the first-time setup in the WSL terminal that opened" -ForegroundColor White
    Write-Host "2. Close that terminal and run:" -ForegroundColor White
    Write-Host "   wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bash $SETUP_SCRIPT" -ForegroundColor Yellow
    Write-Host "3. Run tests with: .\scripts\run-tests.ps1" -ForegroundColor White
}

function Run-Tests {
    param([string]$TestFile)
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Running Tests via WSL" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "WSL Instance: $WSL_INSTANCE" -ForegroundColor Gray
    Write-Host "Project Root: $PROJECT_ROOT" -ForegroundColor Gray
    Write-Host "WSL Path: $WSL_PROJECT_ROOT" -ForegroundColor Gray
    Write-Host ""
    
    if (-not (Test-WSLInstance)) {
        exit 1
    }
    
    # Check if test framework is installed
    $frameworkCheck = wsl -d $WSL_INSTANCE bash -c "command -v $TEST_FRAMEWORK" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: $TEST_FRAMEWORK not installed in $WSL_INSTANCE" -ForegroundColor Red
        Write-Host ""
        Write-Host "Run the setup script:" -ForegroundColor Yellow
        Write-Host "  wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bash $SETUP_SCRIPT" -ForegroundColor White
        exit 1
    }
    
    $version = wsl -d $WSL_INSTANCE $TEST_FRAMEWORK --version
    Write-Host "✅ $TEST_FRAMEWORK installed: $version" -ForegroundColor Green
    Write-Host ""
    
    # Run tests
    if ($TestFile) {
        $testPath = Join-Path $PROJECT_ROOT $TEST_DIR $TestFile
        if (-not (Test-Path $testPath)) {
            Write-Host "ERROR: Test file not found: $testPath" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "🧪 Running test file: $TestFile" -ForegroundColor Cyan
        Write-Host ""
        
        wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bash scripts/test-runner.sh $TestFile
    } else {
        Write-Host "🧪 Running all tests in: $TEST_DIR" -ForegroundColor Cyan
        Write-Host ""
        
        wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bash scripts/test-runner.sh
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
}

function Run-Shellcheck {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Running shellcheck via WSL" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-WSLInstance)) {
        exit 1
    }
    
    wsl -d $WSL_INSTANCE --cd $WSL_PROJECT_ROOT bash scripts/test-runner.sh --shellcheck
    
    $exitCode = $LASTEXITCODE
    
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "✅ shellcheck passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ shellcheck found issues" -ForegroundColor Red
    }
    
    exit $exitCode
}

# Main execution
if ($Help) {
    Show-Usage
    exit 0
}

if ($Setup) {
    Setup-WSLInstance
    exit 0
}

if ($Shellcheck) {
    Run-Shellcheck
    exit 0
}

Run-Tests -TestFile $TestFile

# Test Directory Restructuring and Cleanup Script
# Save as: scripts/restructure_tests.ps1

# Create backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backup_tests_$timestamp"
Write-Host "Creating backup in $backupDir"
Copy-Item -Path "tests" -Destination $backupDir -Recurse

# Step 1: Create new structure
Write-Host "Creating new test directory structure..."
@(
    "tests/integration/api/middleware",
    "tests/integration/agent",
    "tests/integration/tools",
    "tests/unit/api/middleware",
    "tests/unit/agent",
    "tests/unit/tools",
    "tests/unit/config"
) | ForEach-Object {
    New-Item -Path $_ -ItemType Directory -Force | Out-Null
}

# Step 2: Move existing test files
Write-Host "Moving test files to new locations..."
if (Test-Path "tests/test_api/middleware") {
    Move-Item -Path "tests/test_api/middleware/*" -Destination "tests/unit/api/middleware/" -Force
}

if (Test-Path "tests/integration/middleware") {
    Move-Item -Path "tests/integration/middleware/*" -Destination "tests/integration/api/middleware/" -Force
    Remove-Item "tests/integration/middleware" -Force
}

# Step 3: Clean up redundant files
Write-Host "Cleaning up redundant files..."
@(
    "tests/test_api",
    "rate_test_result.txt",
    "i_test-RESULT.TXT",
    "scripts/i_test-RESULT.TXT"
) | ForEach-Object {
    if (Test-Path $_) {
        Remove-Item -Path $_ -Force -Recurse
    }
}

# Step 4: Create READMEs
Write-Host "Creating documentation files..."
@"
# Unit Tests

Unit tests validate individual components in isolation. These tests should:
- Test a single unit of code
- Mock external dependencies
- Run quickly
- Not require external services

## Structure
Each module has its own directory:
- api/: API endpoint and middleware tests
- agent/: Agent component tests
- config/: Configuration system tests
- tools/: Tool implementation tests
"@ | Out-File -FilePath "tests/unit/README.md" -Encoding utf8

@"
# Integration Tests

Integration tests validate component interactions. These tests should:
- Test multiple components working together
- Use test doubles sparingly
- Validate end-to-end flows
- May require external services

## Structure
Each major subsystem has its own directory:
- api/: API integration tests
- agent/: Agent system tests
- tools/: Tool integration tests
"@ | Out-File -FilePath "tests/integration/README.md" -Encoding utf8

# Step 5: Update .gitignore
Write-Host "Updating .gitignore..."
@"

# Test results
*test-RESULT.TXT
*test_result.txt
*-RESULT.TXT

# Test backups
backup_tests_*
"@ | Add-Content -Path ".gitignore"

# Step 6: Verify structure
Write-Host "Verifying new structure..."
if (-not (Test-Path "tests/unit/api/middleware") -or -not (Test-Path "tests/integration/api/middleware")) {
    Write-Error "Directory structure verification failed"
    exit 1
}

Write-Host "Test restructuring and cleanup completed successfully!"
Write-Host "Backup created in: $backupDir"
Write-Host "Review changes and run tests before committing"


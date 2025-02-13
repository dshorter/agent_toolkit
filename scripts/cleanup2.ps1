# Final cleanup for test directories
# Save as: scripts/final_cleanup.ps1

# Move core tests
if (Test-Path "tests/unit/test_core") {
    New-Item -Path "tests/unit/core" -ItemType Directory -Force
    Move-Item -Path "tests/unit/test_core/*" -Destination "tests/unit/core/" -Force
    Remove-Item "tests/unit/test_core" -Recurse -Force
}

# Move config tests
if (Test-Path "tests/unit/test_config") {
    Move-Item -Path "tests/unit/test_config/*" -Destination "tests/unit/config/" -Force
    Remove-Item "tests/unit/test_config" -Recurse -Force
}

# Remove redundant test_api directory
if (Test-Path "tests/unit/test_api") {
    Remove-Item "tests/unit/test_api" -Recurse -Force
}

Write-Host "Final cleanup completed successfully!"
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean up temporary files in the agents-workspace project.

.DESCRIPTION
    Removes Python cache files, test cache, coverage files, and other temporary files.
    Run this script before commits or to free up disk space.

.EXAMPLE
    .\scripts\cleanup.ps1
#>

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "SilentlyContinue"

# Get script location and project root
$ScriptPath = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Agents Workspace Cleanup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

if ($DryRun) {
    Write-Host "[DRY RUN] No files will be deleted" -ForegroundColor Yellow
    Write-Host ""
}

# Directory patterns to remove
$DirPatterns = @(
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".coverage_html"
)

# File patterns to remove
$FilePatterns = @(
    "*.pyc",
    "*.pyo",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
    "*.egg-info"
)

# Counters
$DirsRemoved = 0
$FilesRemoved = 0
$BytesSaved = 0

# Remove directories matching patterns
Write-Host ""
Write-Host "Cleaning directories..." -ForegroundColor Yellow

foreach ($Pattern in $DirPatterns) {
    $Dirs = Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter $Pattern -ErrorAction SilentlyContinue

    foreach ($Dir in $Dirs) {
        $Size = (Get-ChildItem -Path $Dir.FullName -Recurse -File -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum

        if ($Verbose -or $DryRun) {
            $SizeKB = [math]::Round($Size / 1KB, 2)
            Write-Host "  [-] $($Dir.FullName) ($SizeKB KB)" -ForegroundColor DarkGray
        }

        if (-not $DryRun) {
            Remove-Item -Path $Dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }

        $DirsRemoved++
        $BytesSaved += $Size
    }
}

# Remove files matching patterns
Write-Host ""
Write-Host "Cleaning files..." -ForegroundColor Yellow

foreach ($Pattern in $FilePatterns) {
    $Files = Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter $Pattern -ErrorAction SilentlyContinue

    foreach ($File in $Files) {
        $Size = $File.Length

        if ($Verbose -or $DryRun) {
            $SizeKB = [math]::Round($Size / 1KB, 2)
            Write-Host "  [-] $($File.FullName) ($SizeKB KB)" -ForegroundColor DarkGray
        }

        if (-not $DryRun) {
            Remove-Item -Path $File.FullName -Force -ErrorAction SilentlyContinue
        }

        $FilesRemoved++
        $BytesSaved += $Size
    }
}

# Special handling for .next build cache (optional)
$NextDirs = Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter ".next" -ErrorAction SilentlyContinue

if ($NextDirs) {
    Write-Host ""
    Write-Host "Found .next build cache directories:" -ForegroundColor Yellow
    foreach ($Dir in $NextDirs) {
        $Size = (Get-ChildItem -Path $Dir.FullName -Recurse -File -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        $SizeMB = [math]::Round($Size / 1MB, 2)
        Write-Host "  [!] $($Dir.FullName) ($SizeMB MB)" -ForegroundColor DarkYellow
    }
    Write-Host "  Note: Use -IncludeNext to remove .next directories" -ForegroundColor DarkGray
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Cleanup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$SavedMB = [math]::Round($BytesSaved / 1MB, 2)
$SavedKB = [math]::Round($BytesSaved / 1KB, 2)

if ($DryRun) {
    Write-Host "Mode: DRY RUN (no changes made)" -ForegroundColor Yellow
} else {
    Write-Host "Mode: CLEANUP" -ForegroundColor Green
}

Write-Host ""
Write-Host "Directories processed: $DirsRemoved" -ForegroundColor White
Write-Host "Files processed: $FilesRemoved" -ForegroundColor White

if ($BytesSaved -ge 1MB) {
    Write-Host "Space saved: $SavedMB MB" -ForegroundColor Green
} else {
    Write-Host "Space saved: $SavedKB KB" -ForegroundColor Green
}

Write-Host ""

if (-not $DryRun -and ($DirsRemoved -gt 0 -or $FilesRemoved -gt 0)) {
    Write-Host "Cleanup completed successfully!" -ForegroundColor Green
} elseif ($DryRun) {
    Write-Host "Dry run completed. Use without -DryRun to remove files." -ForegroundColor Yellow
} else {
    Write-Host "No temporary files found to clean." -ForegroundColor Gray
}

Write-Host "========================================"
Write-Host "Manual GitHub Actions / CI Validation"
Write-Host "Sprint 3 - CI/CD Learning Platform"
Write-Host "========================================"

if (!(Test-Path "Sprint3_Evidence")) {
    New-Item -ItemType Directory -Path "Sprint3_Evidence" | Out-Null
}

Write-Host "`n[1/6] Python version"
python --version

Write-Host "`n[2/6] Pip version"
python -m pip --version

Write-Host "`n[3/6] Install dependencies"
python -m pip install -r requirements.txt

Write-Host "`n[4/6] Check Python syntax"
python -m compileall .

Write-Host "`n[5/6] Run automated tests"
python -m pytest -v --junitxml=Sprint3_Evidence\manual_ci_pytest_junit.xml

Write-Host "`n[6/6] Run coverage report"
python -m pytest --cov=. --cov-report=term-missing --cov-report=xml:Sprint3_Evidence\manual_ci_coverage.xml

Write-Host "`n========================================"
Write-Host "Manual CI/CD Validation Completed"
Write-Host "Evidence files:"
Write-Host "- Sprint3_Evidence\manual_ci_pytest_junit.xml"
Write-Host "- Sprint3_Evidence\manual_ci_coverage.xml"
Write-Host "- Sprint3_Evidence\manual_ci_full_log.txt"
Write-Host "Expected final result:"
Write-Host "- 278 passed tests"
Write-Host "- 96% total coverage"
Write-Host "========================================"

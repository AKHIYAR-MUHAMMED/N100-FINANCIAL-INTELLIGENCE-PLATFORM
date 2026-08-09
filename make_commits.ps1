# Sprint 5 - 10 commits across deliverables

# Commit 1: NLP Parser outputs (Day 29)
git add output/analysis_parsed.csv output/parse_failures.csv
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(nlp): Day 29 - analysis text parser with regex CAGR extraction and divergence cross-validation"
} else {
    Write-Host "Commit 1: nothing to commit, skipping"
}

# Commit 2: Pros/Cons generator outputs (Day 30)
git add output/pros_cons_generated.csv
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(nlp): Day 30 - auto pros/cons generator with 12+12 rules and confidence scoring for all 92 companies"
} else {
    Write-Host "Commit 2: nothing to commit, skipping"
}

# Commit 3: Cash Flow Intelligence outputs (Day 31)
git add output/cashflow_intelligence.xlsx output/distress_alerts.csv
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(analytics): Day 31 - cash flow intelligence module with CFO quality, CapEx intensity and distress signals"
} else {
    Write-Host "Commit 3: nothing to commit, skipping"
}

# Commit 4: Capital allocation pattern changes (Day 32)
git add output/capital_allocation.csv output/pattern_changes.csv
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(analytics): Day 32 - capital allocation distribution summary and year-over-year pattern change report"
} else {
    Write-Host "Commit 4: nothing to commit, skipping"
}

# Commit 5: NLP source modules + tests
git add src/nlp/parser.py src/nlp/pros_cons_generator.py src/nlp/__init__.py tests/test_nlp.py tests/test_sprint5_integration.py
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(nlp): add src/nlp parser and pros_cons_generator modules with full test coverage"
} else {
    Write-Host "Commit 5: nothing to commit, skipping"
}

# Commit 6: Cash flow analytics source + reports source
git add src/analytics/cashflow_kpis.py src/reports/tearsheet.py src/reports/sector_report.py src/reports/portfolio_report.py
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(reports): add tearsheet, sector report and portfolio PDF generators using ReportLab"
} else {
    Write-Host "Commit 6: nothing to commit, skipping"
}

# Commit 7: Tearsheets COMP01-COMP30 (Day 33-34)
git add "reports/tearsheets/COMP01_tearsheet.pdf" "reports/tearsheets/COMP02_tearsheet.pdf" "reports/tearsheets/COMP03_tearsheet.pdf" "reports/tearsheets/COMP04_tearsheet.pdf" "reports/tearsheets/COMP05_tearsheet.pdf" "reports/tearsheets/COMP06_tearsheet.pdf" "reports/tearsheets/COMP07_tearsheet.pdf" "reports/tearsheets/COMP08_tearsheet.pdf" "reports/tearsheets/COMP09_tearsheet.pdf" "reports/tearsheets/COMP10_tearsheet.pdf" "reports/tearsheets/COMP11_tearsheet.pdf" "reports/tearsheets/COMP12_tearsheet.pdf" "reports/tearsheets/COMP13_tearsheet.pdf" "reports/tearsheets/COMP14_tearsheet.pdf" "reports/tearsheets/COMP15_tearsheet.pdf" "reports/tearsheets/COMP16_tearsheet.pdf" "reports/tearsheets/COMP17_tearsheet.pdf" "reports/tearsheets/COMP18_tearsheet.pdf" "reports/tearsheets/COMP19_tearsheet.pdf" "reports/tearsheets/COMP20_tearsheet.pdf" "reports/tearsheets/COMP21_tearsheet.pdf" "reports/tearsheets/COMP22_tearsheet.pdf" "reports/tearsheets/COMP23_tearsheet.pdf" "reports/tearsheets/COMP24_tearsheet.pdf" "reports/tearsheets/COMP25_tearsheet.pdf" "reports/tearsheets/COMP26_tearsheet.pdf" "reports/tearsheets/COMP27_tearsheet.pdf" "reports/tearsheets/COMP28_tearsheet.pdf" "reports/tearsheets/COMP29_tearsheet.pdf" "reports/tearsheets/COMP30_tearsheet.pdf"
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "data(reports): Day 34 - batch tearsheet PDF generation COMP01-COMP30 (2-page ReportLab, charts, pros/cons)"
} else {
    Write-Host "Commit 7: nothing to commit, skipping"
}

# Commit 8: Tearsheets COMP31-COMP61
git add "reports/tearsheets/COMP31_tearsheet.pdf" "reports/tearsheets/COMP32_tearsheet.pdf" "reports/tearsheets/COMP33_tearsheet.pdf" "reports/tearsheets/COMP34_tearsheet.pdf" "reports/tearsheets/COMP35_tearsheet.pdf" "reports/tearsheets/COMP36_tearsheet.pdf" "reports/tearsheets/COMP37_tearsheet.pdf" "reports/tearsheets/COMP38_tearsheet.pdf" "reports/tearsheets/COMP39_tearsheet.pdf" "reports/tearsheets/COMP40_tearsheet.pdf" "reports/tearsheets/COMP41_tearsheet.pdf" "reports/tearsheets/COMP42_tearsheet.pdf" "reports/tearsheets/COMP43_tearsheet.pdf" "reports/tearsheets/COMP44_tearsheet.pdf" "reports/tearsheets/COMP45_tearsheet.pdf" "reports/tearsheets/COMP46_tearsheet.pdf" "reports/tearsheets/COMP47_tearsheet.pdf" "reports/tearsheets/COMP48_tearsheet.pdf" "reports/tearsheets/COMP49_tearsheet.pdf" "reports/tearsheets/COMP50_tearsheet.pdf" "reports/tearsheets/COMP51_tearsheet.pdf" "reports/tearsheets/COMP52_tearsheet.pdf" "reports/tearsheets/COMP53_tearsheet.pdf" "reports/tearsheets/COMP54_tearsheet.pdf" "reports/tearsheets/COMP55_tearsheet.pdf" "reports/tearsheets/COMP56_tearsheet.pdf" "reports/tearsheets/COMP57_tearsheet.pdf" "reports/tearsheets/COMP58_tearsheet.pdf" "reports/tearsheets/COMP59_tearsheet.pdf" "reports/tearsheets/COMP60_tearsheet.pdf" "reports/tearsheets/COMP61_tearsheet.pdf"
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "data(reports): Day 34 - batch tearsheet PDF generation COMP31-COMP61 (2-page ReportLab, charts, pros/cons)"
} else {
    Write-Host "Commit 8: nothing to commit, skipping"
}

# Commit 9: Tearsheets COMP62-COMP92 + sector PDFs
git add "reports/tearsheets/COMP62_tearsheet.pdf" "reports/tearsheets/COMP63_tearsheet.pdf" "reports/tearsheets/COMP64_tearsheet.pdf" "reports/tearsheets/COMP65_tearsheet.pdf" "reports/tearsheets/COMP66_tearsheet.pdf" "reports/tearsheets/COMP67_tearsheet.pdf" "reports/tearsheets/COMP68_tearsheet.pdf" "reports/tearsheets/COMP69_tearsheet.pdf" "reports/tearsheets/COMP70_tearsheet.pdf" "reports/tearsheets/COMP71_tearsheet.pdf" "reports/tearsheets/COMP72_tearsheet.pdf" "reports/tearsheets/COMP73_tearsheet.pdf" "reports/tearsheets/COMP74_tearsheet.pdf" "reports/tearsheets/COMP75_tearsheet.pdf" "reports/tearsheets/COMP76_tearsheet.pdf" "reports/tearsheets/COMP77_tearsheet.pdf" "reports/tearsheets/COMP78_tearsheet.pdf" "reports/tearsheets/COMP79_tearsheet.pdf" "reports/tearsheets/COMP80_tearsheet.pdf" "reports/tearsheets/COMP81_tearsheet.pdf" "reports/tearsheets/COMP82_tearsheet.pdf" "reports/tearsheets/COMP83_tearsheet.pdf" "reports/tearsheets/COMP84_tearsheet.pdf" "reports/tearsheets/COMP85_tearsheet.pdf" "reports/tearsheets/COMP86_tearsheet.pdf" "reports/tearsheets/COMP87_tearsheet.pdf" "reports/tearsheets/COMP88_tearsheet.pdf" "reports/tearsheets/COMP89_tearsheet.pdf" "reports/tearsheets/COMP90_tearsheet.pdf" "reports/tearsheets/COMP91_tearsheet.pdf" "reports/tearsheets/COMP92_tearsheet.pdf"
git add reports/sector/
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "data(reports): Day 34 - tearsheets COMP62-COMP92 complete + 11 sector analysis PDFs generated"
} else {
    Write-Host "Commit 9: nothing to commit, skipping"
}

# Commit 10: Portfolio summary PDF + final output files (Day 35)
git add reports/portfolio/portfolio_summary.pdf output/valuation_summary.xlsx output/skipped_tearsheets.csv
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat(reports): Day 35 - portfolio summary PDF (92 pages, trend arrows) and Sprint 5 review sign-off"
} else {
    Write-Host "Commit 10: nothing to commit, skipping"
}

Write-Host ""
Write-Host "Done! Final commit log:"
git log --oneline -12

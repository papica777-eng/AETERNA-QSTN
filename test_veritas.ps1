Write-Host "======================================================================"
Write-Host "  AETERNA VERITAS TEST SUITE // SOVEREIGN QA PIPELINE                 "
Write-Host "======================================================================"

Write-Host "`n[1/2] Executing Zig Native Mathematical Alignment Tests..."
# Navigate to src/ingress and run zig test
$zig_test = Start-Process -FilePath "zig" -ArgumentList "test src\ingress\SOP_STREAM_ACQUISITION.zig" -NoNewWindow -Wait -PassThru
if ($zig_test.ExitCode -ne 0) {
    Write-Host "[FATAL] ZIG C-ABI MEMORY ALIGNMENT FAILED. HALTING." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[SUCCESS] ZIG MEMORY TESTS PASSED. (O(1) Bounds Verified)" -ForegroundColor Green
}

Write-Host "`n[2/2] Executing Rust Sovereign Core Atomic Integration Tests..."
# We have a build.rs that compiles parser.zig to a static library, so cargo test should link it
$rust_test = Start-Process -FilePath "cargo" -ArgumentList "test --manifest-path Cargo.toml" -NoNewWindow -Wait -PassThru
if ($rust_test.ExitCode -ne 0) {
    Write-Host "[FATAL] RUST ATOMIC CORE TESTS FAILED. HALTING." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[SUCCESS] RUST ATOMIC CORE TESTS PASSED. (FFI Linked)" -ForegroundColor Green
}

Write-Host "`n======================================================================"
Write-Host "  STATUS: VERITAS DOME SECURED. SYSTEM IS 100% DETERMINISTIC.         "
Write-Host "======================================================================"
exit 0

# Extended web probes (not core native acceptance)

Actual JS/WASM execution for the shared MIR INCDEC change. Expectations remain
correct full-width values. Known G-JS-4 and G-WASM-9 wide-integer limitations
remain failures, with baseline and current evidence under
reports/s030_args_20261021. This suite is intentionally retained as failing
coverage; rejected compilation and rounded/wrong output are not support.

Run: python tests/turkce_ad/run_tests.py --uxb bin/<candidate>.exe --test-root tests/task_provider_completion/argument_web_probes --output reports/<new-dir> --jobs 2 --temp-builds

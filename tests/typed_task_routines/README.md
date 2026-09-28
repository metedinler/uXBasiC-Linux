# Typed task routine tests

These tests cover the real `UXB_TYPED_TASK_ROUTINES_REAL_20260728` patch.

Positive cases:

- typed and multi-argument `EVENT`
- `PIPE` result through the pipe name
- `PIPE` result through `RETURN`
- legacy `INPUT` and `OUTPUT` aliases
- last-assignment-wins result aliasing
- type-name conversion equivalence (`I8(255)` and `value AS I8`)
- typed `THREAD` and `PARALEL` bodies using normal uXBasic statements
- array-typed parameter in the task header
- normal `FUNCTION` formal parameter through `PRINT`
- `CLNG` rounding and `FIX` zero-toward truncation across interpreter paths

Negative cases:

- wrong argument count
- `BYREF` task parameter while native ownership ABI v2 is absent
- duplicate parameter name
- return type on a non-`PIPE` task

## What the runner checks

A non-zero exit code alone proves nothing: an unrelated failure exits non-zero
too, and a backend producing the *wrong* value still exits zero.  So every
check is verified against a recorded expectation in `expected/`:

- `expected/<test>.txt` — the exact program output a positive test must print.
  Both the AST and the MIR backend are compared against the same file, so the
  two backends are required to agree.
- `expected/<test>.err.txt` — a substring that must appear in the compiler
  output of a negative test, so the intended diagnostic is the one that fired.

Line endings are normalized before comparison (the AST backend writes CRLF and
the MIR backend writes LF), and a trailing newline is ignored.

A missing expectation file is a failure, not a silent pass.

## Running

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\typed_task_routines\run_typed_task_tests.ps1 -Uxb .\bin\uxb.exe
```

Add `-EmitMirX64` to also require that each test lowers to a non-empty NASM
listing through the MIR to x64 path.

The runner exits 1 when any check fails and prints a summary naming each one.
It does not rebuild the compiler; give it an existing `uxb.exe` and rebuild
explicitly when source files changed.

`-UpdateExpected` rewrites the expected output files from the compiler's
current behaviour.  Use it only when a change to expected behaviour is
intentional, and review the regenerated files before keeping them — it will
happily record a regression as the new baseline.

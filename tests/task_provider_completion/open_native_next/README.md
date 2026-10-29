# S-030/T2.6.3b next acceptance

`incdec_index_once` must output 10 / 11 / 1. On args4 the actual AST, MIR,
and MIR-native outputs pass; legacy AST-x64 evaluates NextIndex twice.
Evidence: reports/s030_args_20261021/next_array_baseline/summary.json.
This is retained as a failing feature test, not an expected rejection.

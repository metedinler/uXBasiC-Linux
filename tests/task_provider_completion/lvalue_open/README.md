# Existing S-146 step 5 / S-030 open target

shared_class_field is a positive target test, not an expected rejection.
It must ultimately execute both native worker providers with actual per-object
synchronization and correct reference lifetime. Both old and current front-end
reject CLASS sharing explicitly. This remains open and is not included in the
lvalue numeric acceptance. Retained source and expectation are not downgraded.

#!/usr/bin/env python3
from pathlib import Path
out=Path(__file__).with_name('s111_many_bounds_generated.uxb')
lines=['DIM a(0 TO 999) AS I32'] + ['PRINT UBOUND(a)']*1000
out.write_text('\n'.join(lines)+'\n')
print(out)

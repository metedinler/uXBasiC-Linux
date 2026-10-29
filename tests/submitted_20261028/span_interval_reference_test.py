#!/usr/bin/env python3
"""S056/S094 unsigned interval model smoke tests.
Runs on Python as a reference for the intended interval predicate.
Does not compile or execute FreeBASIC/uXBasic.
"""
import unittest

U64_MAX = (1 << 64) - 1

def classify(addr, count, base=1000, length=16, state="live"):
    if count == 0:
        count = 1
    if count > U64_MAX - addr:
        return "overflow"
    end = addr + count
    region_end = base + length
    if state == "live":
        if addr <= region_end and end > base:
            if addr < base:
                return "underflow"
            if end > region_end:
                return "overrun"
            return "ok"
    if state == "released":
        if addr < region_end and end > base:
            return "stale"
    return "external"

class SpanTests(unittest.TestCase):
    def test_cases(self):
        cases = [
            (1000, 4, "live", "ok"),
            (1012, 4, "live", "ok"),
            (1016, 1, "live", "overrun"),
            (1015, 4, "live", "overrun"),
            (999, 4, "live", "underflow"),
            (996, 4, "live", "external"),
            (1200, 4, "live", "external"),
            (1000, 1, "released", "stale"),
            (999, 4, "released", "stale"),
            (1016, 1, "released", "external"),
            (U64_MAX - 1, 4, "live", "overflow"),
            (U64_MAX, 1, "live", "overflow"),
        ]
        for addr, size, state, expected in cases:
            with self.subTest(addr=addr, size=size, state=state):
                self.assertEqual(classify(addr, size, state=state), expected)

if __name__ == "__main__":
    unittest.main()

DECLARE FUNCTION uxconfig_open CDECL ALIAS "uxconfig_open" (BYVAL path AS PTR) AS INTEGER
DECLARE SUB uxconfig_close CDECL ALIAS "uxconfig_close" (BYVAL handle AS INTEGER)

PRINT "UXB_FFI_PTR64_PROBE_START"
DIM h AS INTEGER
h = uxconfig_open(0)
PRINT "HANDLE="; HEX(h)
uxconfig_close(h)
PRINT "UXB_FFI_PTR64_PROBE_PASS"

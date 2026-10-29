' UXClazz generated-code support. Pure uXBasic; no compiler extension.

NAMESPACE uxclazz_support

' S-544 (2026-10-17): HashI64 calls HashString before its definition, so it is announced first (strict DECLARE rule)
DECLARE FUNCTION HashString(value AS STRING) AS U64

FUNCTION HashCombine(seed AS U64, value AS U64) AS U64
    RETURN (seed XOR value) * 1099511628211
END FUNCTION

FUNCTION HashI64(value AS I64) AS U64
    RETURN HashString(STR(value))
END FUNCTION

FUNCTION HashString(value AS STRING) AS U64
    DIM h AS U64
    DIM i AS I32
    h = 1469598103934665603
    FOR i = 1 TO LEN(value)
        h = (h XOR U64(ASC(MID(value, i, 1)))) * 1099511628211
    NEXT
    RETURN h
END FUNCTION

FUNCTION EscapeJson(value AS STRING) AS STRING
    DIM out AS STRING
    DIM i AS I32
    DIM ch AS STRING
    out = ""
    FOR i = 1 TO LEN(value)
        ch = MID(value, i, 1)
        IF ch == CHR(34) THEN
            out = out + "\\" + CHR(34)
        ELSEIF ch == "\\" THEN
            out = out + "\\\\"
        ELSEIF ch == CHR(10) THEN
            out = out + "\\n"
        ELSEIF ch == CHR(13) THEN
            out = out + "\\r"
        ELSEIF ch == CHR(9) THEN
            out = out + "\\t"
        ELSE
            out = out + ch
        END IF
    NEXT
    RETURN out
END FUNCTION

FUNCTION BoolJson(value AS BOOLEAN) AS STRING
    IF value THEN RETURN "true"
    RETURN "false"
END FUNCTION

END NAMESPACE

TYPE Siparis
kod AS I32
tutar AS I32
END TYPE

FUNCTION Dogrula(tutar AS I32, kod AS I32) AS I32
    IF tutar <= 0 THEN
        RETURN -1
    END IF
    IF kod <= 0 THEN
        RETURN -2
    END IF
    RETURN 1
END FUNCTION

DIM kod AS I32
DIM tutar AS I32

kod = 11
tutar = 500

PRINT OFFSETOF(Siparis, "kod")
PRINT OFFSETOF(Siparis, "tutar")
PRINT Dogrula(tutar, kod)
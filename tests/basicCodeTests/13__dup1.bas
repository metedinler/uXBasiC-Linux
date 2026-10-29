FUNCTION Faktoriyel(n AS I32) AS I32
    IF n = 0 OR n = 1 THEN
        RETURN 1
    END IF
    RETURN n * Faktoriyel(n - 1)
END FUNCTION

d = 6
PRINT d
PRINT Faktoriyel(d)
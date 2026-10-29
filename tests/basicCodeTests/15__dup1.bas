FUNCTION Max2(a AS I32, b AS I32) AS I32
    IF a > b THEN
        RETURN a
    END IF
    RETURN b
END FUNCTION

a = 23
b = 89
c = 44
m = Max2(Max2(a,b),c)
PRINT m
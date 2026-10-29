FUNCTION Hesapla(tutar AS I32, oran AS I32) AS I32
    IF tutar <= 0 OR oran <= 0 THEN
        RETURN 0
    END IF
    RETURN (tutar * oran) / 100
END FUNCTION

u = 1000
k = Hesapla(u, 20)
PRINT u
PRINT k
PRINT u + k
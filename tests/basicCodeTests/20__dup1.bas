FUNCTION DugumYaz(id AS I32, seviye AS I32) AS I32
    PRINT id
    IF seviye >= 2 THEN
        RETURN 0
    END IF
    z1 = DugumYaz(id * 2 + 1, seviye + 1)
    z2 = DugumYaz(id * 2 + 2, seviye + 1)
    RETURN 1
END FUNCTION

CALL DugumYaz(0,0)
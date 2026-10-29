DIM i AS I32
DIM stok AS I32

FOR i = 5 TO 0 STEP -2
    stok = i * 10
    PRINT i
    IF stok < 20 THEN
        EXIT FOR
    END IF
NEXT
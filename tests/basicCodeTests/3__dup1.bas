DIM kredi AS I32
DIM gelir AS F64

kredi = 750
gelir = 15000.5

IF kredi >= 800 AND gelir > 20000 THEN
    PRINT 1
ELSEIF kredi >= 700 OR gelir >= 15000 THEN
    PRINT 2
    IF gelir < 16000 THEN
        PRINT 21
    END IF
ELSEIF kredi <> -1 THEN
    PRINT 3
ELSE
    PRINT 4
END IF
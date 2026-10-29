DIM segment AS I32
segment = 3

SELECT CASE segment
    CASE 1
        PRINT 100
    CASE 2
        PRINT 200
    CASE IS > 2
        PRINT 300
    CASE ELSE
        PRINT 400
END SELECT
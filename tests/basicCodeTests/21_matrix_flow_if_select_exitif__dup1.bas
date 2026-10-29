a = 12

IF a > 0 THEN
    PRINT "if-enter"
    EXIT IF
    PRINT "if-unreach"
ELSE
    PRINT "if-else"
END IF

SELECT CASE a
    CASE IS > 10
        PRINT "case-gt10"
    CASE ELSE
        PRINT "case-else"
END SELECT

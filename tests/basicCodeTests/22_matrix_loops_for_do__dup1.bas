sumFor = 0
FOR i = 1 TO 5
    sumFor = sumFor + i
    IF i = 3 THEN
        EXIT FOR
    END IF
NEXT

sumDo = 0
j = 0
DO
    j = j + 1
    sumDo = sumDo + j
    IF j = 2 THEN
        EXIT DO
    END IF
LOOP

PRINT "for="; sumFor
PRINT "do="; sumDo

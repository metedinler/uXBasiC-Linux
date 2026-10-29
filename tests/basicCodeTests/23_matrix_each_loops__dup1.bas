sumEach = 0
FOR EACH v, idx IN 10, 20, 30
    sumEach = sumEach + v + idx
NEXT

sumDoEach = 0
DO EACH u IN 4, 5, 6
    sumDoEach = sumDoEach + u
LOOP

PRINT "each="; sumEach
PRINT "doeach="; sumDoEach

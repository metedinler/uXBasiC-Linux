DEFINT A-Z
SETSTRINGSIZE 64

mask = 15
DIM a AS I8 = 1
DIM b AS U8 = 2
DIM c AS I16 = 3
DIM d AS I32 = 4
DIM e AS I64 = 5
DIM f AS F64 = 2.5
DIM ok AS BOOLEAN = 0
DIM s AS STRING = "ab"

DIM arr(0 TO 2) AS I32
REDIM PRESERVE arr(0 TO 4) AS I32

x = a + b + c + d + e
ok = (x > 0)

y = (1 SHL 4) OR 1
z = 10 MOD 4
t = 1 ROL 3

IF y > 10 THEN
    PRINT "y>10";
ELSE
    PRINT "y<=10"
END IF

SELECT CASE y
    CASE IS > 10
        PRINT "case-is"
    CASE ELSE
        PRINT "case-else"
END SELECT

sumForEach = 0
FOR EACH v, idx IN 1, 2, 3
    sumForEach = sumForEach + v + idx
NEXT

sumDoEach = 0
DO EACH u IN 4, 5, 6
    sumDoEach = sumDoEach + u
    EXIT DO
LOOP

PRINT LEN(s)
PRINT ASC("A")
PRINT ABS(-7)
PRINT INT(9)
PRINT SGN(-5)
PRINT VAL("42")
PRINT STR(123)
PRINT UCASE("ab")
PRINT LCASE("AB")
PRINT MID("ABCDE",2,2)
PRINT SPACE(2)
PRINT STRING(2,66)
PRINT SQR(16)
PRINT SIN(0)
PRINT COS(0)
PRINT TAN(0)
PRINT ATN(1)
PRINT EXP(1)
PRINT LOG(1)
PRINT RND(1)
PRINT TIMER()

label1:
DECLARE SUB proc1()
GOSUB sub1
GOTO done1
sub1:
x = x + 1
RETURN
done1:
PRINT x

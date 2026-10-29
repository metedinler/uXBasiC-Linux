DIM gCounter AS I32
DIM gResult AS I32

gCounter = 10

SUB Touch(v AS I32)
    PRINT v
END SUB

SUB AccumulateAndPrint(a AS I32, b AS I32)
    DIM localSum AS I32

    localSum = a + b
    gCounter = localSum
    CALL Touch(localSum)
    PRINT localSum
END SUB

FUNCTION ScaleAndBias(x AS I32) AS I32
    DIM localY AS I32

    localY = x + 7
    RETURN localY
END FUNCTION

CALL AccumulateAndPrint(3, 4)
gResult = ScaleAndBias(gCounter)
PRINT gResult
END

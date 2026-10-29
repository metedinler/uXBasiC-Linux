FUNCTION SumTo(n AS I32) AS I32
    s = 0
    FOR i = 1 TO n
        s = s + i
    NEXT i
    RETURN s
END FUNCTION

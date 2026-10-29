FUNCTION Fibonacci(n AS I32) AS I32
    IF n <= 0 THEN
        RETURN 0
    ELSEIF n = 1 THEN
        RETURN 1
    END IF
    RETURN Fibonacci(n - 1) + Fibonacci(n - 2)
END FUNCTION

n = 10
PRINT Fibonacci(n)
TYPE Row
    a(0 TO 2) AS I32
END TYPE

DIM r AS Row

r.a(0) = 3
r.a(1) = 4
r.a(2) = 5

PRINT r.a(0) + r.a(1) + r.a(2)
END

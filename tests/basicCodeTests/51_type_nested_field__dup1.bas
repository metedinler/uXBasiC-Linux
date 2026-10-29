TYPE Point
    x AS F64
    y AS F64
END TYPE

TYPE Box
    p AS Point
    id AS I32
END TYPE

DIM b AS Box

b.p.x = 1.25
b.p.y = 2.75
b.id = 9

PRINT b.p.x + b.p.y
PRINT b.id
END

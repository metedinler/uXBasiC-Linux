TYPE Point
    x AS F64
    y AS F64
    z AS F32
    i AS I32
END TYPE

DIM p AS Point

p.x = 1.5
p.y = 2.75
p.z = 3.25
p.i = 7

PRINT p.x + p.y
PRINT p.z
PRINT p.i
END

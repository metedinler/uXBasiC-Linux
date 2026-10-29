TYPE V2
    X AS I32
    Y AS I32
END TYPE

CLASS BOX
    X AS I32
END CLASS

DIM arr(0 TO 1) AS I32
DIM p AS V2
DIM b AS BOX = NEW BOX()

p.X = 10
arr(0) = p.X + 2
p.Y = arr(0) + 3
PRINT p.X
PRINT p.Y

b.X = p.Y + 5
arr(1) = b.X
PRINT b.X
PRINT arr(1)

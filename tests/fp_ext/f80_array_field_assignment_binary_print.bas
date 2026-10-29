TYPE Precise80
    x AS F80
    y AS F80
    z AS F80
END TYPE

DIM p AS Precise80
DIM arr(0 TO 2) AS F80

p.x = 1.50
p.y = 2.25
p.z = p.x + p.y
PRINT p.z

arr(0) = 5.50
arr(1) = 6.25
arr(2) = arr(0) + arr(1)
PRINT arr(2)
END

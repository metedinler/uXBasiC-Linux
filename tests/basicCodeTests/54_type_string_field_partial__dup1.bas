TYPE LabelledPoint
    name AS STRING
    x AS F64
END TYPE

DIM p AS LabelledPoint

p.name = "Origin"
p.x = 1.5

PRINT p.name
PRINT p.x
END

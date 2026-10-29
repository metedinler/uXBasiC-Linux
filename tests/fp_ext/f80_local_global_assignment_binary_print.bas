DIM gA AS F80
DIM gB AS F80
DIM gC AS F80

gA = 1.25
gB = 2.50
gC = gA + gB
PRINT gC

SUB ProbeF80Local()
    DIM a AS F80
    DIM b AS F80
    DIM c AS F80
    a = 3.25
    b = 4.75
    c = a + b
    PRINT c
END SUB

CALL ProbeF80Local()
END

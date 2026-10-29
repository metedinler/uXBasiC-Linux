TYPE Point
    x AS I32
    y AS I32
END TYPE
CLASS Counter
PUBLIC:
    value AS I32
    CONSTRUCTOR()
        value = 0
    END CONSTRUCTOR
    SUB Inc()
        value = value + 1
    END SUB
    FUNCTION GetValue() AS I32
        RETURN value
    END FUNCTION
END CLASS
DIM p AS Point
p.x = 3
p.y = 4
DIM c AS Counter = NEW Counter()
c.Inc()
PRINT "OOP_ROUTE_OK"

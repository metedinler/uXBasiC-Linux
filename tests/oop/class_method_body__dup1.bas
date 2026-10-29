CLASS Vec2
    x AS F64
    y AS F64

    CONSTRUCTOR(x0 AS F64, y0 AS F64)
        THIS.x = x0
        THIS.y = y0
    END METHOD

    METHOD Length2() AS F64
        RETURN THIS.x * THIS.x + THIS.y * THIS.y
    END METHOD

    DESTRUCTOR()
        PRINT "Vec2 destroyed"
    END METHOD
END CLASS

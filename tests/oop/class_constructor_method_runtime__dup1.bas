CLASS Vec2
PUBLIC
    x AS I32
    y AS I32

    CONSTRUCTOR(x0 AS I32, y0 AS I32)
        THIS.x = x0
        THIS.y = y0
    END CONSTRUCTOR

    METHOD Length2() AS I32
        RETURN THIS.x * THIS.x + THIS.y * THIS.y
    END METHOD

    DESTRUCTOR()
        THIS.x = 0
        THIS.y = 0
    END DESTRUCTOR
END CLASS

DIM v AS Vec2
v = NEW Vec2(3, 4)
PRINT v.Length2()
DELETE v

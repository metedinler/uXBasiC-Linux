DIM dep AS I32
DIM ceyrek AS I32
DIM toplam AS I32

FOR dep = 1 TO 3
    toplam = 0
    FOR ceyrek = 1 TO 4
        toplam = toplam + dep + ceyrek
    NEXT
    PRINT toplam
NEXT
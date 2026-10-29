TYPE Personel
id AS I32
puan AS I32
END TYPE

DIM p AS Personel
PRINT OFFSETOF(Personel, "id")
PRINT OFFSETOF(Personel, "puan")
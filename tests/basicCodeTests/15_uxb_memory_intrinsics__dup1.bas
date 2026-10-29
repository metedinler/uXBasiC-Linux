TYPE Pair
lo AS I16
hi AS I16
END TYPE

TYPE Packet
tag AS I8
pairs(0 TO 1) AS Pair
word AS I32
END TYPE

MAIN
base = VARPTR(root)
POKEW base + OFFSETOF(Packet, "pairs(1).hi"), 13398
POKED base + OFFSETOF(Packet, "word"), 287454020
u = PEEKW(base + OFFSETOF(Packet, "pairs(1).hi"))
v = PEEKD(base + OFFSETOF(Packet, "word"))

x = 4096
POKEB x, 65
POKEW x + 2, 4660
POKED x + 8, 305419896

MEMFILLB x + 16, 7, 4
MEMCOPYB x, x + 32, 1
POKES x + 40, "HI"

MEMFILLW x + 48, 4660, 2
MEMCOPYW x + 48, x + 56, 2
MEMFILLD x + 64, 305419896, 1
MEMCOPYD x + 64, x + 72, 1

a = PEEKB(x)
b = PEEKW(x + 2)
c = PEEKD(x + 8)

p = VARPTR(a)
q = SADD("abc")
r = LPTR(label1)
t = CODEPTR(proc1)
SETNEWOFFSET a, 8192

PRINT "a,b,c="; a; b; c
PRINT "u,v="; u; v
PRINT "ptrs="; p; q; r; t

label1:
DECLARE SUB proc1()
END MAIN

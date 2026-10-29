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
s = SADD("abc")
l = LPTR(label1)
label1:
DECLARE SUB proc1()
k = CODEPTR(proc1)
SETNEWOFFSET a, 8192
q = VARPTR(a)
r = (1 SHL 4) OR 1
m = 10 MOD 4
t = 1 ROL 3
INC a
DEC a
' S-544 (2026-10-17): a DECLARE needs a definition in the program (strict DECLARE rule)
SUB proc1()
END SUB

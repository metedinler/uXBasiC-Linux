RANDOMIZE 42
bugun = TIMER()
r = RND(1)
gelecek = bugun + 45

PRINT bugun
PRINT gelecek
PRINT r
IF gelecek > bugun THEN
    PRINT 1
END IF
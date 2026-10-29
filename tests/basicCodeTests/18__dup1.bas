DIM d AS DICT
CALL DICTSET(d, "server_01", 10)
CALL DICTSET(d, "db_master", 50)

z = DICTGET(d, "db_master")
PRINT z
EVENT OnTick, 1
    PRINT "tick"
END EVENT

THREAD Worker, 2
    PRINT "worker"
END THREAD

PARALEL Job, 4
    PRINT "job"
END PARALEL

PIPE Normalize, 5
    value = INPUT
    OUTPUT = value + 1
END PIPE

SLOT EVENT <U8 32>
SLOT PIPE 16
MAIN
    ON EVENT OnTick
    TRIGGER EVENT OnTick
    OFF EVENT OnTick
    ON PIPE Normalize
    sonuc = 10 | Normalize
    PRINT sonuc
END MAIN

INCLUDE "include/modules/uxcollections.uxmh"

MAIN
    DIM listHandle AS U64
    DIM stackHandle AS U64
    DIM queueHandle AS U64
    DIM dictHandle AS U64
    DIM setHandle AS U64
    DIM treeHandle AS U64

    PRINT "UXCOLLECTIONS_STAGE=VERSION"
    ASSERT uxcollections.Version() = 1

    PRINT "UXCOLLECTIONS_STAGE=LIST"
    listHandle = uxcollections.ListNew()
    ASSERT listHandle <> 0
    uxcollections.ListPushF64(listHandle, 1.5)
    uxcollections.ListPushF64(listHandle, 2.5)
    ASSERT uxcollections.ListCount(listHandle) = 2
    ASSERT ABS(uxcollections.ListGetF64(listHandle, 0) - 1.5) < 0.000001
    uxcollections.ListFree(listHandle)

    PRINT "UXCOLLECTIONS_STAGE=STACK"
    stackHandle = uxcollections.StackNew()
    ASSERT stackHandle <> 0
    uxcollections.StackPushF64(stackHandle, 7.0)
    ASSERT ABS(uxcollections.StackPopF64(stackHandle) - 7.0) < 0.000001
    uxcollections.StackFree(stackHandle)

    PRINT "UXCOLLECTIONS_STAGE=QUEUE"
    queueHandle = uxcollections.QueueNew()
    ASSERT queueHandle <> 0
    uxcollections.QueuePushF64(queueHandle, 3.0)
    uxcollections.QueuePushF64(queueHandle, 4.0)
    ASSERT ABS(uxcollections.QueuePopF64(queueHandle) - 3.0) < 0.000001
    uxcollections.QueueFree(queueHandle)

    PRINT "UXCOLLECTIONS_STAGE=DICT"
    dictHandle = uxcollections.DictNew()
    ASSERT dictHandle <> 0
    uxcollections.DictSetF64(dictHandle, "mean", 12.5)
    ASSERT uxcollections.DictHas(dictHandle, "mean") = 1
    ASSERT ABS(uxcollections.DictGetF64(dictHandle, "mean") - 12.5) < 0.000001
    uxcollections.DictFree(dictHandle)

    PRINT "UXCOLLECTIONS_STAGE=SET"
    setHandle = uxcollections.SetNew()
    ASSERT setHandle <> 0
    uxcollections.SetAdd(setHandle, "uXBasic")
    ASSERT uxcollections.SetContains(setHandle, "uXBasic") = 1
    ASSERT uxcollections.SetContains(setHandle, "missing") = 0
    uxcollections.SetFree(setHandle)

    PRINT "UXCOLLECTIONS_STAGE=TREE"
    treeHandle = uxcollections.TreeNew()
    ASSERT treeHandle <> 0
    uxcollections.TreeSetF64(treeHandle, "b", 2.0)
    uxcollections.TreeSetF64(treeHandle, "a", 1.0)
    ASSERT ABS(uxcollections.TreeGetF64(treeHandle, "a") - 1.0) < 0.000001
    uxcollections.TreeFree(treeHandle)

    PRINT "PASS_UXCOLLECTIONS"
END MAIN

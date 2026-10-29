INCLUDE "include/modules/uxgraph.uxmh"

g = uxgraph.Create(5, 0)

uxgraph.AddEdge(g, 0, 1)
uxgraph.AddEdge(g, 1, 2)
uxgraph.AddEdge(g, 2, 3)
uxgraph.AddEdge(g, 3, 4)

PRINT uxgraph.VCount(g)
PRINT uxgraph.ECount(g)
PRINT uxgraph.Degree(g, 1)
PRINT uxgraph.ShortestDistance(g, 0, 4)
PRINT uxgraph.Components(g)

uxgraph.Free(g)

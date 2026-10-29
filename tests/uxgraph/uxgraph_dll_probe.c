#include <math.h>
#include <stdio.h>
#include "../../runtime_ext/uxgraph/uxgraph.h"

#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    const char *csv_path = "uxb/dist/runtime_ext/uxgraph_probe_edges.csv";
    void *g = uxgraph_create(5, 0);
    REQUIRE(g != NULL, 2);
    REQUIRE(uxgraph_add_edge(g,0,1) && uxgraph_add_edge(g,1,2), 3);
    REQUIRE(uxgraph_add_edge(g,2,3) && uxgraph_add_edge(g,3,4), 4);
    REQUIRE(uxgraph_add_edge(g,4,0), 5);
    REQUIRE(uxgraph_vcount(g)==5 && uxgraph_ecount(g)==5 && !uxgraph_is_directed(g), 6);
    REQUIRE(uxgraph_has_edge(g,0,1) && uxgraph_has_edge(g,1,0), 7);
    REQUIRE(uxgraph_degree(g,0)==2 && uxgraph_shortest_distance(g,0,3)==2, 8);
    REQUIRE(uxgraph_path_exists(g,1,4) && uxgraph_is_connected(g), 9);
    REQUIRE(uxgraph_components_count(g)==1 && fabs(uxgraph_density(g)-0.5)<1e-12, 10);
    REQUIRE(uxgraph_triangle_count(g)==0 && uxgraph_self_loops(g)==0, 11);

    void *dist = uxgraph_bfs_distances(g,0);
    void *deg = uxgraph_degree_vector(g,0);
    REQUIRE(dist && deg, 12);
    REQUIRE(uxgraph_vec_count(dist)==5 && uxgraph_vec_get(dist,3)==2.0, 13);
    REQUIRE(uxgraph_vec_count(deg)==5 && uxgraph_vec_get(deg,0)==2.0, 14);
    uxgraph_vec_free(dist);
    uxgraph_vec_free(deg);

    REQUIRE(uxgraph_write_edgelist_csv(g,csv_path), 15);
    void *loaded = uxgraph_read_edgelist_csv(csv_path,0);
    REQUIRE(loaded && uxgraph_vcount(loaded)==5 && uxgraph_ecount(loaded)==5, 16);
    uxgraph_free(loaded);
    remove(csv_path);

    void *complete = uxgraph_make_complete(4,0);
    REQUIRE(complete && uxgraph_ecount(complete)==6, 17);
    REQUIRE(uxgraph_triangle_count(complete)==4, 18);
    REQUIRE(fabs(uxgraph_transitivity(complete)-1.0)<1e-12, 19);

    printf("v=%d e=%d degree0=%d dist0to3=%d density=%.6f\n",
           uxgraph_vcount(g),uxgraph_ecount(g),uxgraph_degree(g,0),
           uxgraph_shortest_distance(g,0,3),uxgraph_density(g));
    puts("PASS_UXGRAPH");
    uxgraph_free(complete);
    uxgraph_free(g);
    return 0;
}

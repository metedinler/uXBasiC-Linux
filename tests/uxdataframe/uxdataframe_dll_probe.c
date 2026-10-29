#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "../../runtime_ext/uxdataframe/uxdataframe.h"

int main(void) {
    FILE* f = fopen("uxb/dist/runtime_ext/uxdf_probe.csv", "w");
    if (!f) return 2;
    fprintf(f, "id,x,y,grp\n1,1.0,2.0,A\n2,2.0,4.0,A\n3,3.0,6.0,B\n");
    fclose(f);

    if (uxdf_duckdb_available() != 1) return 3;
    printf("duckdb_available=1\n");
    printf("duckdb_version=%s\n", uxdf_duckdb_version());
    void* df = uxdf_load_csv("uxb/dist/runtime_ext/uxdf_probe.csv", 1);
    if (!df) { printf("load failed: %s\n", uxdf_last_error(NULL)); return 4; }
    if (uxdf_row_count(df) != 3 || uxdf_col_count(df) != 4) return 5;
    printf("rows=3 cols=4\n");
    const char* col0 = uxdf_col_name(df,0);
    const char* col1 = uxdf_col_name(df,1);
    if (strcmp(col0, "id") != 0 || strcmp(col1, "x") != 0) return 6;
    printf("col0=%s col1=%s\n", col0, col1);
    if (fabs(uxdf_get_f64(df,1,2) - 4.0) > 1e-9 || strcmp(uxdf_get_text(df,0,3), "A") != 0) return 7;
    printf("cell=4.000000 text=A\n");
    void* q = uxdf_query(df, "SELECT grp, AVG(y) AS my FROM uxdf_1 GROUP BY grp ORDER BY grp");
    // Query table name is unknown to the user, so also test wrapper helpers.
    void* h = uxdf_head(df, 2);
    if (!q || !h || uxdf_row_count(h) != 2) return 8;
    printf("head_rows=2\n");
    void* m = uxdf_to_f64_matrix(uxdf_select(df, "x,y"));
    if (!m || uxdf_matrix_rows(m) != 3 || uxdf_matrix_cols(m) != 2 || fabs(uxdf_matrix_get(m,0,0) - 1.0) > 1e-9) return 9;
    printf("matrix=3x2 first=1.000000\n");
    uxdf_matrix_free(m);
    if (q) uxdf_free(q);
    if (h) uxdf_free(h);
    uxdf_to_csv(df, "uxb/dist/runtime_ext/uxdf_out.csv");
    uxdf_free(df);
    printf("PASS_UXDATAFRAME_DUCKDB\n");
    return 0;
}

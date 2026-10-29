#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../runtime_ext/uxllama/uxllama.h"
int main(int argc, char **argv) {
    char out[65536]; char err[2048];
    uxllama_handle h = uxllama_create();
    if (!h) return 2;
    if (argc > 1) uxllama_set_model_path(h, argv[1]);
    if (argc > 2) uxllama_set_cli_path(h, argv[2]);
    uxllama_set_low_memory_profile(h, 0);
    printf("version=%d\n", uxllama_version());
    printf("model_exists=%d\n", uxllama_model_exists(h));
    if (argc > 1 && uxllama_model_exists(h)) {
        int n = uxllama_prompt(h, "Write one short Turkish sentence about uXBasic.", out, sizeof(out));
        if (n <= 0) { uxllama_last_error(h, err, sizeof(err)); printf("ERR=%s\n", err); uxllama_free(h); return 1; }
        printf("OUT=%s\n", out);
    } else {
        uxllama_last_error(h, err, sizeof(err));
        printf("NO_MODEL_TEST_ONLY\n");
    }
    uxllama_free(h); return 0;
}

#include "uxffi.h"
#include <ffi.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#define UXFFI_HANDLE_CAPACITY 65535u
#define UXFFI_HANDLE_TAG 0x40000000u
#define UXFFI_HANDLE_TAG_MASK 0xC0000000u
#define UXFFI_HANDLE_INDEX_MASK 0x0000FFFFu
#define UXFFI_HANDLE_GENERATION_MASK 0x00003FFFu
#define UXFFI_MODULE_CAPACITY 64
#define UXFFI_MAX_STRING_BYTES (16u * 1024u * 1024u)

typedef struct {
    void *ptr;
    uint16_t generation;
    uint8_t owned;
} uxffi_handle_entry;

typedef struct {
    char name[MAX_PATH];
    HMODULE module;
} uxffi_module_entry;

typedef int (__cdecl *uxffi_fb_ready_fn)(void);

static uxffi_handle_entry g_handles[UXFFI_HANDLE_CAPACITY];
static uint32_t g_next_handle = 1;
static uxffi_module_entry g_modules[UXFFI_MODULE_CAPACITY];
static int g_module_count = 0;
static SRWLOCK g_lock = SRWLOCK_INIT;
static SRWLOCK g_string_call_lock = SRWLOCK_INIT;

static void set_error(char *buffer, int capacity, const char *message) {
    if (!buffer || capacity <= 0) return;
    if (!message) message = "unknown uxffi error";
    snprintf(buffer, (size_t)capacity, "%s", message);
    buffer[capacity - 1] = '\0';
}

static HMODULE get_cached_module(const char *dll_name) {
    HMODULE result = NULL;
    AcquireSRWLockShared(&g_lock);
    for (int i = 0; i < g_module_count; ++i) {
        if (_stricmp(g_modules[i].name, dll_name) == 0) {
            result = g_modules[i].module;
            break;
        }
    }
    ReleaseSRWLockShared(&g_lock);
    if (result) return result;

    AcquireSRWLockExclusive(&g_lock);
    for (int i = 0; i < g_module_count; ++i) {
        if (_stricmp(g_modules[i].name, dll_name) == 0) {
            result = g_modules[i].module;
            break;
        }
    }
    if (!result && g_module_count < UXFFI_MODULE_CAPACITY) {
        result = LoadLibraryA(dll_name);
        if (result) {
            snprintf(g_modules[g_module_count].name, MAX_PATH, "%s", dll_name);
            g_modules[g_module_count].name[MAX_PATH - 1] = '\0';
            g_modules[g_module_count].module = result;
            ++g_module_count;
        }
    }
    ReleaseSRWLockExclusive(&g_lock);
    return result;
}

static const char *module_basename(const char *path) {
    const char *base = path;
    const char *p;
    if (!path) return "";
    for (p = path; *p; ++p) {
        if (*p == '\\' || *p == '/') base = p + 1;
    }
    return base;
}

static int is_required_freebasic_module(const char *dll_name) {
    static const char *const names[] = {
        "uxsystem.dll", "uxfs.dll", "uxpath.dll", "uxprocess.dll",
        "uxlog.dll", "uxconfig.dll", "uxdatetime.dll", "uxuuid.dll"
    };
    const char *base = module_basename(dll_name);
    size_t i;
    for (i = 0; i < sizeof(names) / sizeof(names[0]); ++i) {
        if (_stricmp(base, names[i]) == 0) return 1;
    }
    return 0;
}

static int call_optional_freebasic_ready(HMODULE module, const char *dll_name) {
    FARPROC proc;
    uxffi_fb_ready_fn fn;
    if (!module) return 0;
    proc = GetProcAddress(module, "uxfb_runtime_ready");
    if (!proc) return is_required_freebasic_module(dll_name) ? 0 : 1;
    if (sizeof(fn) != sizeof(proc)) return 0;
    memcpy(&fn, &proc, sizeof(fn));
    return fn() != 0;
}

static uint32_t next_generation(uint16_t previous) {
    uint32_t value = ((uint32_t)previous + 1u) & UXFFI_HANDLE_GENERATION_MASK;
    if (value == 0) value = 1;
    return value;
}

static uint32_t make_token(uint32_t index, uint32_t generation) {
    return UXFFI_HANDLE_TAG |
           ((generation & UXFFI_HANDLE_GENERATION_MASK) << 16) |
           (index & UXFFI_HANDLE_INDEX_MASK);
}

static int decode_token(uint64_t value, uint32_t *index_out, uint32_t *generation_out) {
    uint32_t token;
    if ((value >> 32) != 0) return 0;
    token = (uint32_t)value;
    uint32_t index;
    uint32_t generation;
    if ((token & UXFFI_HANDLE_TAG_MASK) != UXFFI_HANDLE_TAG) return 0;
    index = token & UXFFI_HANDLE_INDEX_MASK;
    generation = (token >> 16) & UXFFI_HANDLE_GENERATION_MASK;
    if (index == 0 || index >= UXFFI_HANDLE_CAPACITY || generation == 0) return 0;
    if (index_out) *index_out = index;
    if (generation_out) *generation_out = generation;
    return 1;
}

static uint32_t store_handle(void *ptr, int owned) {
    uint32_t token = 0;
    if (!ptr) return 0;
    AcquireSRWLockExclusive(&g_lock);
    for (uint32_t attempts = 0; attempts < UXFFI_HANDLE_CAPACITY - 1; ++attempts) {
        uint32_t index = g_next_handle++;
        uint32_t generation;
        if (g_next_handle >= UXFFI_HANDLE_CAPACITY) g_next_handle = 1;
        if (!g_handles[index].ptr) {
            generation = next_generation(g_handles[index].generation);
            g_handles[index].generation = (uint16_t)generation;
            g_handles[index].ptr = ptr;
            g_handles[index].owned = owned ? 1u : 0u;
            token = make_token(index, generation);
            break;
        }
    }
    ReleaseSRWLockExclusive(&g_lock);
    return token;
}

/* S-653: A handle token is a 32-bit value (so it fits an interpreter I32/U32 variable), which makes it
   numerically indistinguishable from a real user-mode address in 0x40000000..0x7FFFFFFF.  The old rule
   ("every value with the tag bits is a token") rejected genuine pointers (VARPTR, heap addresses) as
   "stale or invalid pointer handle token" whenever the process happened to place memory in that band.
   A PTR argument is therefore classified by looking at the handle table:
     - the value names a LIVE handle (slot in use, same generation)         -> TOKEN: use the registered pointer
     - not live, but the address is committed memory in this process         -> RAW:   pass the value through
     - not live, not committed memory, and the slot was handed out before     -> STALE: the token was released
     - anything else                                                          -> RAW:   pass the value through
   The only remaining ambiguity is a real address numerically equal to a currently LIVE token, which resolves
   in favour of the token. */
enum { UXFFI_CLASS_RAW = 0, UXFFI_CLASS_TOKEN = 1, UXFFI_CLASS_STALE = 2 };

static int address_is_committed(uint64_t value) {
    MEMORY_BASIC_INFORMATION info;
    if (VirtualQuery((LPCVOID)(uintptr_t)value, &info, sizeof(info)) != sizeof(info)) return 0;
    return info.State == MEM_COMMIT;
}

static int classify_pointer_arg(uint64_t value, void **resolved) {
    uint32_t index;
    uint32_t generation;
    int live = 0;
    int used_before = 0;
    *resolved = (void *)(uintptr_t)value;
    if (!decode_token(value, &index, &generation)) return UXFFI_CLASS_RAW;
    AcquireSRWLockShared(&g_lock);
    if (g_handles[index].ptr && g_handles[index].generation == generation) {
        *resolved = g_handles[index].ptr;
        live = 1;
    }
    used_before = g_handles[index].generation != 0;
    ReleaseSRWLockShared(&g_lock);
    if (live) return UXFFI_CLASS_TOKEN;
    if (address_is_committed(value)) return UXFFI_CLASS_RAW;
    return used_before ? UXFFI_CLASS_STALE : UXFFI_CLASS_RAW;
}

static int memory_region_is_readable(const MEMORY_BASIC_INFORMATION *info) {
    DWORD protect;
    if (!info || info->State != MEM_COMMIT) return 0;
    protect = info->Protect;
    if ((protect & PAGE_GUARD) != 0 || (protect & PAGE_NOACCESS) != 0) return 0;
    return 1;
}

/* Snapshot a foreign C string while the exporting DLL call is still serialized.
   ReadProcessMemory avoids an access violation if a DLL returns an invalid pointer. */
static char *duplicate_bounded_string(const char *source) {
    char *copy;
    size_t capacity = 256u;
    size_t length = 0u;
    HANDLE process;
    if (!source) return NULL;
    copy = (char *)malloc(capacity);
    if (!copy) return NULL;
    process = GetCurrentProcess();

    while (length < UXFFI_MAX_STRING_BYTES) {
        MEMORY_BASIC_INFORMATION info;
        const char *cursor = source + length;
        uintptr_t region_end;
        size_t available;
        size_t chunk;
        SIZE_T bytes_read = 0;
        void *zero;

        if (VirtualQuery(cursor, &info, sizeof(info)) != sizeof(info) || !memory_region_is_readable(&info)) {
            free(copy);
            return NULL;
        }
        region_end = (uintptr_t)info.BaseAddress + info.RegionSize;
        if (region_end <= (uintptr_t)cursor) {
            free(copy);
            return NULL;
        }
        available = (size_t)(region_end - (uintptr_t)cursor);
        chunk = available;
        if (chunk > 65536u) chunk = 65536u;
        if (chunk > UXFFI_MAX_STRING_BYTES - length) chunk = UXFFI_MAX_STRING_BYTES - length;
        if (chunk == 0u) {
            free(copy);
            return NULL;
        }
        if (length + chunk + 1u > capacity) {
            size_t new_capacity = capacity;
            char *grown;
            while (new_capacity < length + chunk + 1u) {
                if (new_capacity >= UXFFI_MAX_STRING_BYTES / 2u) {
                    new_capacity = UXFFI_MAX_STRING_BYTES + 1u;
                    break;
                }
                new_capacity *= 2u;
            }
            grown = (char *)realloc(copy, new_capacity);
            if (!grown) {
                free(copy);
                return NULL;
            }
            copy = grown;
            capacity = new_capacity;
        }
        if (!ReadProcessMemory(process, cursor, copy + length, chunk, &bytes_read) || bytes_read == 0u) {
            free(copy);
            return NULL;
        }
        zero = memchr(copy + length, '\0', (size_t)bytes_read);
        if (zero) {
            size_t final_length = (size_t)((char *)zero - copy);
            copy[final_length] = '\0';
            return copy;
        }
        length += (size_t)bytes_read;
    }

    free(copy);
    return NULL;
}

static int string_token_length_locked(uint32_t token, size_t *length_out) {
    uint32_t index;
    uint32_t generation;
    const char *source;
    size_t length = 0u;
    if (!decode_token((uint64_t)token, &index, &generation)) return 0;
    if (!g_handles[index].ptr || g_handles[index].generation != generation || !g_handles[index].owned) return 0;
    source = (const char *)g_handles[index].ptr;
    while (length < UXFFI_MAX_STRING_BYTES && source[length] != '\0') ++length;
    if (length >= UXFFI_MAX_STRING_BYTES) return 0;
    if (length_out) *length_out = length;
    return 1;
}

int uxffi_string_length(uint32_t token) {
    size_t length = 0u;
    int ok;
    if (token == 0u) return 1;
    AcquireSRWLockShared(&g_lock);
    ok = string_token_length_locked(token, &length);
    ReleaseSRWLockShared(&g_lock);
    if (!ok || length >= (size_t)INT_MAX) return 0;
    return (int)(length + 1u);
}

int uxffi_copy_string(uint32_t token, char *out_text, int out_capacity) {
    size_t length = 0u;
    int ok;
    if (!out_text || out_capacity <= 0) return 0;
    out_text[0] = '\0';
    if (token == 0u) return 1;

    AcquireSRWLockShared(&g_lock);
    ok = string_token_length_locked(token, &length);
    if (ok && (size_t)out_capacity > length) {
        memcpy(out_text, g_handles[token & UXFFI_HANDLE_INDEX_MASK].ptr, length + 1u);
    } else {
        ok = 0;
    }
    ReleaseSRWLockShared(&g_lock);
    if (!ok) return 0;
    uxffi_release_handle(token);
    return 1;
}

int uxffi_release_handle(uint32_t token) {
    uint32_t index;
    uint32_t generation;
    void *owned_ptr = NULL;
    int released = 0;
    if (!decode_token((uint64_t)token, &index, &generation)) return 0;
    AcquireSRWLockExclusive(&g_lock);
    if (g_handles[index].ptr && g_handles[index].generation == generation) {
        if (g_handles[index].owned) owned_ptr = g_handles[index].ptr;
        g_handles[index].ptr = NULL;
        g_handles[index].owned = 0;
        released = 1;
    }
    ReleaseSRWLockExclusive(&g_lock);
    if (owned_ptr) free(owned_ptr);
    return released;
}

void uxffi_clear_handles(void) {
    AcquireSRWLockExclusive(&g_lock);
    for (uint32_t i = 1; i < UXFFI_HANDLE_CAPACITY; ++i) {
        if (g_handles[i].ptr && g_handles[i].owned) free(g_handles[i].ptr);
        g_handles[i].ptr = NULL;
        g_handles[i].owned = 0;
    }
    g_next_handle = 1;
    ReleaseSRWLockExclusive(&g_lock);
}

void uxffi_shutdown(void) {
    HMODULE modules[UXFFI_MODULE_CAPACITY];
    int module_count;
    uxffi_clear_handles();
    AcquireSRWLockExclusive(&g_lock);
    module_count = g_module_count;
    for (int i = 0; i < module_count; ++i) modules[i] = g_modules[i].module;
    memset(g_modules, 0, sizeof(g_modules));
    g_module_count = 0;
    ReleaseSRWLockExclusive(&g_lock);
    for (int i = 0; i < module_count; ++i) {
        if (modules[i]) FreeLibrary(modules[i]);
    }
}

int uxffi_version(void) { return UXFFI_API_VERSION; }
int uxffi_max_args(void) { return UXFFI_MAX_ARGS; }

static ffi_type *kind_to_ffi_type(int kind) {
    switch (kind) {
        case UXFFI_I32: return &ffi_type_sint32;
        case UXFFI_U32: return &ffi_type_uint32;
        case UXFFI_I64: return &ffi_type_sint64;
        case UXFFI_U64: return &ffi_type_uint64;
        case UXFFI_F64: return &ffi_type_double;
        case UXFFI_PTR:
        case UXFFI_STRPTR: return &ffi_type_pointer;
        case UXFFI_VOID: return &ffi_type_void;
        default: return NULL;
    }
}

static int release_like_symbol(const char *symbol) {
    size_t n = strlen(symbol);
    const char *suffixes[] = {"_free", "_destroy", "_release", "_close"};
    for (size_t i = 0; i < sizeof(suffixes) / sizeof(suffixes[0]); ++i) {
        size_t m = strlen(suffixes[i]);
        if (n >= m && _stricmp(symbol + n - m, suffixes[i]) == 0) return 1;
    }
    return _stricmp(symbol, "free") == 0 || _stricmp(symbol, "close") == 0;
}

int uxffi_invoke10(
    const char *dll_name, const char *symbol_name, int return_kind, int arg_count,
    const int *arg_kinds, const uint64_t *arg_u64, const double *arg_f64,
    uint64_t *return_u64, double *return_f64, char *error_text, int error_capacity
) {
    HMODULE module;
    FARPROC proc;
    ffi_type *ret_type;
    ffi_type *arg_types[UXFFI_MAX_ARGS];
    void *arg_values[UXFFI_MAX_ARGS];
    int32_t values_i32[UXFFI_MAX_ARGS];
    uint32_t values_u32[UXFFI_MAX_ARGS];
    int64_t values_i64[UXFFI_MAX_ARGS];
    uint64_t values_u64[UXFFI_MAX_ARGS];
    double values_f64[UXFFI_MAX_ARGS];
    void *values_ptr[UXFFI_MAX_ARGS];
    ffi_cif cif;
    union { int32_t i32; uint32_t u32; int64_t i64; uint64_t u64; double f64; void *ptr; } result;
    int lock_string_call = 0;

    if (return_u64) *return_u64 = 0;
    if (return_f64) *return_f64 = 0.0;
    if (error_text && error_capacity > 0) error_text[0] = '\0';
    if (!dll_name || !*dll_name || !symbol_name || !*symbol_name) {
        set_error(error_text, error_capacity, "dll or symbol is empty");
        return 0;
    }
    if (arg_count < 0 || arg_count > UXFFI_MAX_ARGS) {
        set_error(error_text, error_capacity, "argument count exceeds ABI10");
        return 0;
    }
    if (arg_count > 0 && (!arg_kinds || !arg_u64 || !arg_f64)) {
        set_error(error_text, error_capacity, "argument arrays are missing");
        return 0;
    }

    module = get_cached_module(dll_name);
    if (!module) {
        set_error(error_text, error_capacity, "LoadLibraryA failed or module cache is full");
        return 0;
    }
    if (!call_optional_freebasic_ready(module, dll_name)) {
        set_error(error_text, error_capacity, "required uxfb_runtime_ready export is missing or returned failure");
        return 0;
    }
    proc = GetProcAddress(module, symbol_name);
    if (!proc) {
        set_error(error_text, error_capacity, "GetProcAddress failed");
        return 0;
    }

    ret_type = kind_to_ffi_type(return_kind);
    if (!ret_type) {
        set_error(error_text, error_capacity, "invalid return kind");
        return 0;
    }

    for (int i = 0; i < arg_count; ++i) {
        int kind = arg_kinds[i];
        arg_types[i] = kind_to_ffi_type(kind);
        if (!arg_types[i] || kind == UXFFI_VOID) {
            set_error(error_text, error_capacity, "invalid argument kind");
            return 0;
        }
        switch (kind) {
            case UXFFI_I32: values_i32[i] = (int32_t)arg_u64[i]; arg_values[i] = &values_i32[i]; break;
            case UXFFI_U32: values_u32[i] = (uint32_t)arg_u64[i]; arg_values[i] = &values_u32[i]; break;
            case UXFFI_I64: values_i64[i] = (int64_t)arg_u64[i]; arg_values[i] = &values_i64[i]; break;
            case UXFFI_U64: values_u64[i] = arg_u64[i]; arg_values[i] = &values_u64[i]; break;
            case UXFFI_F64: values_f64[i] = arg_f64[i]; arg_values[i] = &values_f64[i]; break;
            case UXFFI_PTR:
                if (classify_pointer_arg(arg_u64[i], &values_ptr[i]) == UXFFI_CLASS_STALE) {
                    set_error(error_text, error_capacity, "stale or invalid pointer handle token");
                    return 0;
                }
                arg_values[i] = &values_ptr[i];
                break;
            case UXFFI_STRPTR: values_ptr[i] = (void *)(uintptr_t)arg_u64[i]; arg_values[i] = &values_ptr[i]; break;
            default: set_error(error_text, error_capacity, "unsupported argument kind"); return 0;
        }
    }

    if (ffi_prep_cif(&cif, FFI_DEFAULT_ABI, (unsigned int)arg_count, ret_type, arg_types) != FFI_OK) {
        set_error(error_text, error_capacity, "ffi_prep_cif failed");
        return 0;
    }
    memset(&result, 0, sizeof(result));

    lock_string_call = (return_kind == UXFFI_STRPTR || is_required_freebasic_module(dll_name));
    if (lock_string_call) AcquireSRWLockExclusive(&g_string_call_lock);
    ffi_call(&cif, FFI_FN(proc), return_kind == UXFFI_VOID ? NULL : &result, arg_values);

    switch (return_kind) {
        case UXFFI_VOID: break;
        case UXFFI_I32: if (return_u64) *return_u64 = (uint64_t)(int64_t)result.i32; break;
        case UXFFI_U32: if (return_u64) *return_u64 = result.u32; break;
        case UXFFI_I64: if (return_u64) *return_u64 = (uint64_t)result.i64; break;
        case UXFFI_U64: if (return_u64) *return_u64 = result.u64; break;
        case UXFFI_F64: if (return_f64) *return_f64 = result.f64; break;
        case UXFFI_PTR: {
            uint32_t token = store_handle(result.ptr, 0);
            if (result.ptr && token == 0) {
                if (lock_string_call) ReleaseSRWLockExclusive(&g_string_call_lock);
                set_error(error_text, error_capacity, "interpreter handle table is full");
                return 0;
            }
            if (return_u64) *return_u64 = token;
            break;
        }
        case UXFFI_STRPTR: {
            char *copy = duplicate_bounded_string((const char *)result.ptr);
            uint32_t token = 0;
            if (result.ptr && !copy) {
                ReleaseSRWLockExclusive(&g_string_call_lock);
                set_error(error_text, error_capacity, "STRPTR result is invalid, too long, or out of memory");
                return 0;
            }
            if (copy) token = store_handle(copy, 1);
            if (copy && token == 0) {
                free(copy);
                ReleaseSRWLockExclusive(&g_string_call_lock);
                set_error(error_text, error_capacity, "interpreter handle table is full");
                return 0;
            }
            if (return_u64) *return_u64 = token;
            break;
        }
        default: break;
    }
    if (lock_string_call) ReleaseSRWLockExclusive(&g_string_call_lock);

    if (release_like_symbol(symbol_name)) {
        /* Destructors in the standard library consume their first PTR handle.
           Do not invalidate unrelated/buffer pointer arguments. */
        for (int i = 0; i < arg_count; ++i) {
            void *ignored_ptr;
            if (arg_kinds[i] == UXFFI_PTR && classify_pointer_arg(arg_u64[i], &ignored_ptr) == UXFFI_CLASS_TOKEN) {
                uxffi_release_handle((uint32_t)arg_u64[i]);
                break;
            }
        }
    }
    return 1;
}

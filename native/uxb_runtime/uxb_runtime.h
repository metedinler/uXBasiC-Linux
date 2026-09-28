#pragma once
#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32)
  #if defined(UXB_RT_BUILD_DLL)
    #define UXB_RT_API extern "C" __declspec(dllexport)
  #else
    #define UXB_RT_API extern "C" __declspec(dllimport)
  #endif
  #define UXB_RT_CDECL __cdecl
#else
  #define UXB_RT_API extern "C" __attribute__((visibility("default")))
  #define UXB_RT_CDECL
#endif

#define UXB_RT_MAX_SLOTS 256
#define UXB_RT_SUCCESS 1
#define UXB_RT_FAILURE 0

#define UXB_RT_TASK_EVENT 1
#define UXB_RT_TASK_PIPE 2
#define UXB_RT_TASK_THREAD 3
#define UXB_RT_TASK_PARALEL 4

typedef int (UXB_RT_CDECL *uxb_task_callback)(
    int slot_id,
    int input_value,
    int* output_value,
    void* user_data
);

UXB_RT_API int UXB_RT_CDECL uxb_rt_init(void);
UXB_RT_API int UXB_RT_CDECL uxb_rt_shutdown(void);
UXB_RT_API int UXB_RT_CDECL uxb_rt_backend(char* out, int out_len);

UXB_RT_API int UXB_RT_CDECL uxb_task_register(int slot_id, int task_type, const char* name);
UXB_RT_API int UXB_RT_CDECL uxb_slot_bind(int slot_id, int task_type, const char* name);
UXB_RT_API int UXB_RT_CDECL uxb_task_set_callback(int slot_id, uxb_task_callback callback, void* user_data);
UXB_RT_API int UXB_RT_CDECL uxb_slot_control(int slot_id, int state);
UXB_RT_API int UXB_RT_CDECL uxb_task_on(int slot_id);
UXB_RT_API int UXB_RT_CDECL uxb_task_off(int slot_id);
UXB_RT_API int UXB_RT_CDECL uxb_slot_on(int slot_id);
UXB_RT_API int UXB_RT_CDECL uxb_slot_off(int slot_id);

UXB_RT_API int UXB_RT_CDECL uxb_task_trigger(int slot_id, int input_value, int* output_value);
UXB_RT_API int UXB_RT_CDECL uxb_thread_start(int slot_id, int input_value, int* output_value);
UXB_RT_API int UXB_RT_CDECL uxb_pipe_run(int slot_id, int input_value, int* output_value);
UXB_RT_API int UXB_RT_CDECL uxb_parallel_run(int slot_id, int input_value, int* output_value);

UXB_RT_API int UXB_RT_CDECL uxb_shell_run(
    const char* command,
    const char* run_path,
    int timeout_ms,
    char* out,
    int out_len,
    char* err,
    int err_len,
    int* exit_code
);

UXB_RT_API int UXB_RT_CDECL uxb_shell_start(
    const char* command,
    const char* run_path,
    const char* out_path,
    const char* err_path,
    int* exit_code
);

UXB_RT_API int UXB_RT_CDECL uxb_text_file_write(const char* path, const char* text);

UXB_RT_API const char* UXB_RT_CDECL uxb_last_error(void);

// S-030 Faz 2A: gorev ABI v2 (uxb_runtime_task_v2.cpp). Thunk sozlesmesi o dosyanin basinda.
// Deger turleri: 0=VOID, 1=I64, 2=F64, 3=STRING. stringArgMask: bit i => i. arguman STRING (kopyalanir).
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_spawn(void* thunk, const void* argblock, int64_t bytes, const char* name, int64_t resultKind, int64_t stringArgMask);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_fail_cstr(const char* message);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_fail_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_cancel_point(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_wait(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_join(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_result(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_cancel(int64_t handle);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_task_status(int64_t handle);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_task_error(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_group_create(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_group_add(int64_t group, int64_t task);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_group_join(int64_t group);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_shutdown(int64_t normalExit);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_worker_count(void);
/* S-146 Model D: depo basina kilit tablosu (uxb_runtime_sync.cpp). ids: kilit kimlikleri
   (lockOrderId / MUTEX degeri), names: statik kimliklere paralel "AD1,AD2". mode 0 = otomatik
   deyim kilidi (ayni gorev icin yeniden girilebilir), 1 = acik LOCK (ikinci kez = SELF_DEADLOCK). */
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sync_enter(const int64_t* ids, int64_t count, const char* names, int64_t mode);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sync_leave(const int64_t* ids, int64_t count, int64_t mode);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_lock_mark(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_lock_release_to(int64_t mark);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_mutex_new(void);
/* S-160: is parcacigina ozel THROW/ASSERT istisna durumu (uxb_runtime_task_v2.cpp). */
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_active(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_set_active(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_set_value(int64_t bits, int64_t isString);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_uncaught(int64_t inTask);
/* S-163: RND/RANDOMIZE, AST/MIR ile ayni uretec, gorev basina durum. */
UXB_RT_API double UXB_RT_CDECL __uxb_rt_rnd_f64(int64_t hasArg, double arg);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_randomize_seed(int64_t hasSeed, int64_t seed);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_set_workers(int64_t count);
// S-156: rutin icindeki END (K5 kapanisi + cikis; donmez).
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_program_end(void);

// Native MIR x64 runtime ABI. Integer values and pointers use 64-bit slots to
// match the Microsoft x64 calling convention used by the NASM backend.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_cstr(const char* value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_newline(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_f64(double value);
// S-142b: floating text (PRINT and STR/concat): F64 16 / F32 7 significant digits,
// no padding zeros, exponent at least two digits. F32 rounds the value to single first.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_f32(double value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_f32(double value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_input_i64(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_cls(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_locate(int64_t row, int64_t column);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_color(int64_t foreground, int64_t background);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_getkey_i64(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_inkey_i64(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_timer_i64(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_rnd_i64(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_randomize(int64_t seed);

// S-157: STRING degiskeni/dizi elemani/alan icin sahipli metin deposu (yuva adresi sahiptir).
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_str_store(const char** slot, const char* src);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_str_release(const char** slot);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_temp(const char* value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_strlen(const char* value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_val_i64(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_asc(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_chr(int64_t value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_left(const char* value, int64_t count);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_right(const char* value, int64_t count);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_mid(const char* value, int64_t start, int64_t count);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_instr(const char* value, const char* needle, int64_t start);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_lcase(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_ucase(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_ltrim(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_rtrim(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_trim(const char* value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_space(int64_t count);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_hex(int64_t value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_oct(int64_t value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_bin(int64_t value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_concat(const char* left, const char* right);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_str_compare(const char* left, const char* right);

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_memcopy(void* dst, const void* src, int64_t bytes);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_memfill(void* dst, int64_t value, int64_t bytes);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_peek_i64(const int64_t* address);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_poke_i64(int64_t* address, int64_t value);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_mem_read_sequence(const void* address, int64_t length);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_mem_write_sequence(void* address, const char* source, int64_t length);

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_open(const char* path, const char* mode, int64_t channel, int64_t record_len);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_close(int64_t channel);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_seek(int64_t channel, int64_t position);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_eof(int64_t channel);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_lof(int64_t channel);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_get(int64_t channel, int64_t position, int64_t bytes);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_put(int64_t channel, int64_t position, int64_t bytes, int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_delete(const char* path);
/* S-146 adim 2: metin dosyasi PRINT # / INPUT # */
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_print_begin(int64_t channel);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_print_text(const char* text, const char* sep);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_print_end(void);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_file_input_line(int64_t channel);
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_u64(int64_t value);

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sqrt_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sin_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_cos_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_tan_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_atn_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_log_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exp_i64(int64_t value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_pow_i64(int64_t left, int64_t right);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_assert_i64(int64_t condition);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_host_call(const char* name);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_host_call4(const char* name, int64_t a, int64_t b, int64_t c);

// S-019 native LIST/DICT/SET collections. Handle: 0 = invalid, positive =
// (slot index + 1); handles are never reused/freed (matches the language's
// own LIST_NEW/DICT_NEW/SET_NEW surface, which has no FREE/DISPOSE call).
// Value kind tags: 1 = I64, 2 = F64 (packed as the double's raw bit pattern,
// not a numeric cast), 3 = STRING (packed as a `const char*` reinterpreted as
// int64_t -- on input it is copied immediately into the collection's own
// storage; on output it points into the same thread-local hold-text ring
// every other string-returning __uxb_rt_* function already uses).
// Every function below is a pure library call: on failure (invalid/wrong-kind
// handle, out-of-range index, missing key) it returns a plain 0 (or -1 for
// the *_len functions, since a real length is never negative) and never
// prints/exits/aborts. The emitted x64 code checks that status itself and, on
// failure, calls __uxb_rt_runtime_error_exit with a message naming the
// specific operation that failed.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_new(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_len(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_get(int64_t handle, int64_t index, int64_t* out_value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_set(int64_t handle, int64_t index, int64_t kind, int64_t packed_value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_add(int64_t handle, int64_t kind, int64_t packed_value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_remove(int64_t handle, int64_t index);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_clear(int64_t handle);

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_new(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_len(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_has(int64_t handle, const char* key);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_get(int64_t handle, const char* key, int64_t* out_value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_set(int64_t handle, const char* key, int64_t kind, int64_t packed_value);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_clear(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_key_at(int64_t handle, int64_t index, const char** out_key);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_value_at(int64_t handle, int64_t index, int64_t* out_value);

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_new(void);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_len(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_has(int64_t handle, const char* member);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_add(int64_t handle, const char* member);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_remove(int64_t handle, const char* member);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_clear(int64_t handle);
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_member_at(int64_t handle, int64_t index, const char** out_member);

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_runtime_error_exit(const char* message);

// STR() / concatenation / DICT-SET key text of an F64 value: the language's
// floating text rule (16 significant digits, no padding zeros), identical to
// what __uxb_rt_print_f64 prints and to the interpreters' text (S-142b).
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_f64(double value);

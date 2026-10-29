#pragma once
#include <cstddef>
#include <string>

// Internal native STRING boundary: preserve explicit lengths across providers.
namespace uxb {
std::string copy_text(const char* text);
const char* hold_text_span(const std::string& text);
// Only storage that remains immutable and alive until process exit may use
// this registry (compiled constants and the existing persistent task records).
void register_persistent_text(const char* text, std::size_t length);
}

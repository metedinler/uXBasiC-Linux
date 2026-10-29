' SDL3 backup runtime wrapper.
NAMESPACE uxsdl3
CONST INIT_AUDIO = 16
CONST INIT_VIDEO = 32
CONST INIT_JOYSTICK = 512
CONST INIT_HAPTIC = 4096
CONST INIT_GAMEPAD = 8192
CONST INIT_EVENTS = 16384
CONST INIT_SENSOR = 32768
CONST INIT_CAMERA = 65536

' SDL_Scancode values for KeyDown/KeyPressed/PushKey (physical key positions; generated from SDL3/SDL_scancode.h).
CONST SCANCODE_UNKNOWN = 0
CONST SCANCODE_A = 4
CONST SCANCODE_B = 5
CONST SCANCODE_C = 6
CONST SCANCODE_D = 7
CONST SCANCODE_E = 8
CONST SCANCODE_F = 9
CONST SCANCODE_G = 10
CONST SCANCODE_H = 11
CONST SCANCODE_I = 12
CONST SCANCODE_J = 13
CONST SCANCODE_K = 14
CONST SCANCODE_L = 15
CONST SCANCODE_M = 16
CONST SCANCODE_N = 17
CONST SCANCODE_O = 18
CONST SCANCODE_P = 19
CONST SCANCODE_Q = 20
CONST SCANCODE_R = 21
CONST SCANCODE_S = 22
CONST SCANCODE_T = 23
CONST SCANCODE_U = 24
CONST SCANCODE_V = 25
CONST SCANCODE_W = 26
CONST SCANCODE_X = 27
CONST SCANCODE_Y = 28
CONST SCANCODE_Z = 29
CONST SCANCODE_1 = 30
CONST SCANCODE_2 = 31
CONST SCANCODE_3 = 32
CONST SCANCODE_4 = 33
CONST SCANCODE_5 = 34
CONST SCANCODE_6 = 35
CONST SCANCODE_7 = 36
CONST SCANCODE_8 = 37
CONST SCANCODE_9 = 38
CONST SCANCODE_0 = 39
CONST SCANCODE_RETURN = 40
CONST SCANCODE_ESCAPE = 41
CONST SCANCODE_BACKSPACE = 42
CONST SCANCODE_TAB = 43
CONST SCANCODE_SPACE = 44
CONST SCANCODE_MINUS = 45
CONST SCANCODE_EQUALS = 46
CONST SCANCODE_LEFTBRACKET = 47
CONST SCANCODE_RIGHTBRACKET = 48
CONST SCANCODE_BACKSLASH = 49
CONST SCANCODE_NONUSHASH = 50
CONST SCANCODE_SEMICOLON = 51
CONST SCANCODE_APOSTROPHE = 52
CONST SCANCODE_GRAVE = 53
CONST SCANCODE_COMMA = 54
CONST SCANCODE_PERIOD = 55
CONST SCANCODE_SLASH = 56
CONST SCANCODE_CAPSLOCK = 57
CONST SCANCODE_F1 = 58
CONST SCANCODE_F2 = 59
CONST SCANCODE_F3 = 60
CONST SCANCODE_F4 = 61
CONST SCANCODE_F5 = 62
CONST SCANCODE_F6 = 63
CONST SCANCODE_F7 = 64
CONST SCANCODE_F8 = 65
CONST SCANCODE_F9 = 66
CONST SCANCODE_F10 = 67
CONST SCANCODE_F11 = 68
CONST SCANCODE_F12 = 69
CONST SCANCODE_PRINTSCREEN = 70
CONST SCANCODE_SCROLLLOCK = 71
CONST SCANCODE_PAUSE = 72
CONST SCANCODE_INSERT = 73
CONST SCANCODE_HOME = 74
CONST SCANCODE_PAGEUP = 75
CONST SCANCODE_DELETE = 76
CONST SCANCODE_END = 77
CONST SCANCODE_PAGEDOWN = 78
CONST SCANCODE_RIGHT = 79
CONST SCANCODE_LEFT = 80
CONST SCANCODE_DOWN = 81
CONST SCANCODE_UP = 82
CONST SCANCODE_NUMLOCKCLEAR = 83
CONST SCANCODE_KP_DIVIDE = 84
CONST SCANCODE_KP_MULTIPLY = 85
CONST SCANCODE_KP_MINUS = 86
CONST SCANCODE_KP_PLUS = 87
CONST SCANCODE_KP_ENTER = 88
CONST SCANCODE_KP_1 = 89
CONST SCANCODE_KP_2 = 90
CONST SCANCODE_KP_3 = 91
CONST SCANCODE_KP_4 = 92
CONST SCANCODE_KP_5 = 93
CONST SCANCODE_KP_6 = 94
CONST SCANCODE_KP_7 = 95
CONST SCANCODE_KP_8 = 96
CONST SCANCODE_KP_9 = 97
CONST SCANCODE_KP_0 = 98
CONST SCANCODE_KP_PERIOD = 99
CONST SCANCODE_NONUSBACKSLASH = 100
CONST SCANCODE_APPLICATION = 101
CONST SCANCODE_POWER = 102
CONST SCANCODE_KP_EQUALS = 103
CONST SCANCODE_F13 = 104
CONST SCANCODE_F14 = 105
CONST SCANCODE_F15 = 106
CONST SCANCODE_F16 = 107
CONST SCANCODE_F17 = 108
CONST SCANCODE_F18 = 109
CONST SCANCODE_F19 = 110
CONST SCANCODE_F20 = 111
CONST SCANCODE_F21 = 112
CONST SCANCODE_F22 = 113
CONST SCANCODE_F23 = 114
CONST SCANCODE_F24 = 115
CONST SCANCODE_EXECUTE = 116
CONST SCANCODE_HELP = 117
CONST SCANCODE_MENU = 118
CONST SCANCODE_SELECT = 119
CONST SCANCODE_STOP = 120
CONST SCANCODE_AGAIN = 121
CONST SCANCODE_UNDO = 122
CONST SCANCODE_CUT = 123
CONST SCANCODE_COPY = 124
CONST SCANCODE_PASTE = 125
CONST SCANCODE_FIND = 126
CONST SCANCODE_MUTE = 127
CONST SCANCODE_VOLUMEUP = 128
CONST SCANCODE_VOLUMEDOWN = 129
CONST SCANCODE_KP_COMMA = 133
CONST SCANCODE_KP_EQUALSAS400 = 134
CONST SCANCODE_INTERNATIONAL1 = 135
CONST SCANCODE_INTERNATIONAL2 = 136
CONST SCANCODE_INTERNATIONAL3 = 137
CONST SCANCODE_INTERNATIONAL4 = 138
CONST SCANCODE_INTERNATIONAL5 = 139
CONST SCANCODE_INTERNATIONAL6 = 140
CONST SCANCODE_INTERNATIONAL7 = 141
CONST SCANCODE_INTERNATIONAL8 = 142
CONST SCANCODE_INTERNATIONAL9 = 143
CONST SCANCODE_LANG1 = 144
CONST SCANCODE_LANG2 = 145
CONST SCANCODE_LANG3 = 146
CONST SCANCODE_LANG4 = 147
CONST SCANCODE_LANG5 = 148
CONST SCANCODE_LANG6 = 149
CONST SCANCODE_LANG7 = 150
CONST SCANCODE_LANG8 = 151
CONST SCANCODE_LANG9 = 152
CONST SCANCODE_ALTERASE = 153
CONST SCANCODE_SYSREQ = 154
CONST SCANCODE_CANCEL = 155
CONST SCANCODE_CLEAR = 156
CONST SCANCODE_PRIOR = 157
CONST SCANCODE_RETURN2 = 158
CONST SCANCODE_SEPARATOR = 159
CONST SCANCODE_OUT = 160
CONST SCANCODE_OPER = 161
CONST SCANCODE_CLEARAGAIN = 162
CONST SCANCODE_CRSEL = 163
CONST SCANCODE_EXSEL = 164
CONST SCANCODE_KP_00 = 176
CONST SCANCODE_KP_000 = 177
CONST SCANCODE_THOUSANDSSEPARATOR = 178
CONST SCANCODE_DECIMALSEPARATOR = 179
CONST SCANCODE_CURRENCYUNIT = 180
CONST SCANCODE_CURRENCYSUBUNIT = 181
CONST SCANCODE_KP_LEFTPAREN = 182
CONST SCANCODE_KP_RIGHTPAREN = 183
CONST SCANCODE_KP_LEFTBRACE = 184
CONST SCANCODE_KP_RIGHTBRACE = 185
CONST SCANCODE_KP_TAB = 186
CONST SCANCODE_KP_BACKSPACE = 187
CONST SCANCODE_KP_A = 188
CONST SCANCODE_KP_B = 189
CONST SCANCODE_KP_C = 190
CONST SCANCODE_KP_D = 191
CONST SCANCODE_KP_E = 192
CONST SCANCODE_KP_F = 193
CONST SCANCODE_KP_XOR = 194
CONST SCANCODE_KP_POWER = 195
CONST SCANCODE_KP_PERCENT = 196
CONST SCANCODE_KP_LESS = 197
CONST SCANCODE_KP_GREATER = 198
CONST SCANCODE_KP_AMPERSAND = 199
CONST SCANCODE_KP_DBLAMPERSAND = 200
CONST SCANCODE_KP_VERTICALBAR = 201
CONST SCANCODE_KP_DBLVERTICALBAR = 202
CONST SCANCODE_KP_COLON = 203
CONST SCANCODE_KP_HASH = 204
CONST SCANCODE_KP_SPACE = 205
CONST SCANCODE_KP_AT = 206
CONST SCANCODE_KP_EXCLAM = 207
CONST SCANCODE_KP_MEMSTORE = 208
CONST SCANCODE_KP_MEMRECALL = 209
CONST SCANCODE_KP_MEMCLEAR = 210
CONST SCANCODE_KP_MEMADD = 211
CONST SCANCODE_KP_MEMSUBTRACT = 212
CONST SCANCODE_KP_MEMMULTIPLY = 213
CONST SCANCODE_KP_MEMDIVIDE = 214
CONST SCANCODE_KP_PLUSMINUS = 215
CONST SCANCODE_KP_CLEAR = 216
CONST SCANCODE_KP_CLEARENTRY = 217
CONST SCANCODE_KP_BINARY = 218
CONST SCANCODE_KP_OCTAL = 219
CONST SCANCODE_KP_DECIMAL = 220
CONST SCANCODE_KP_HEXADECIMAL = 221
CONST SCANCODE_LCTRL = 224
CONST SCANCODE_LSHIFT = 225
CONST SCANCODE_LALT = 226
CONST SCANCODE_LGUI = 227
CONST SCANCODE_RCTRL = 228
CONST SCANCODE_RSHIFT = 229
CONST SCANCODE_RALT = 230
CONST SCANCODE_RGUI = 231
CONST SCANCODE_MODE = 257
CONST SCANCODE_SLEEP = 258
CONST SCANCODE_WAKE = 259
CONST SCANCODE_CHANNEL_INCREMENT = 260
CONST SCANCODE_CHANNEL_DECREMENT = 261
CONST SCANCODE_MEDIA_PLAY = 262
CONST SCANCODE_MEDIA_PAUSE = 263
CONST SCANCODE_MEDIA_RECORD = 264
CONST SCANCODE_MEDIA_FAST_FORWARD = 265
CONST SCANCODE_MEDIA_REWIND = 266
CONST SCANCODE_MEDIA_NEXT_TRACK = 267
CONST SCANCODE_MEDIA_PREVIOUS_TRACK = 268
CONST SCANCODE_MEDIA_STOP = 269
CONST SCANCODE_MEDIA_EJECT = 270
CONST SCANCODE_MEDIA_PLAY_PAUSE = 271
CONST SCANCODE_MEDIA_SELECT = 272
CONST SCANCODE_AC_NEW = 273
CONST SCANCODE_AC_OPEN = 274
CONST SCANCODE_AC_CLOSE = 275
CONST SCANCODE_AC_EXIT = 276
CONST SCANCODE_AC_SAVE = 277
CONST SCANCODE_AC_PRINT = 278
CONST SCANCODE_AC_PROPERTIES = 279
CONST SCANCODE_AC_SEARCH = 280
CONST SCANCODE_AC_HOME = 281
CONST SCANCODE_AC_BACK = 282
CONST SCANCODE_AC_FORWARD = 283
CONST SCANCODE_AC_STOP = 284
CONST SCANCODE_AC_REFRESH = 285
CONST SCANCODE_AC_BOOKMARKS = 286
CONST SCANCODE_SOFTLEFT = 287
CONST SCANCODE_SOFTRIGHT = 288
CONST SCANCODE_CALL = 289
CONST SCANCODE_ENDCALL = 290
CONST SCANCODE_RESERVED = 400

FUNCTION AdapterVersion() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_adapter_version", I32, CDECL)
END FUNCTION
FUNCTION RuntimeVersion() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_runtime_version", I32, CDECL)
END FUNCTION
FUNCTION Revision() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_revision", STRPTR, CDECL)
END FUNCTION
FUNCTION Init(flags AS U32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_init", I32, CDECL, "U32", U32(flags))
END FUNCTION
SUB Quit()
    CALL(DLL, "uxsdl3.dll", "uxsdl3_quit", VOID, CDECL)
END SUB
FUNCTION LastError() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_last_error", STRPTR, CDECL)
END FUNCTION

' ---- Window ----
' Handles are raw SDL pointer values carried as I64; 0 means "no window/renderer".
FUNCTION CreateWindow(title AS STRING, w AS I32, h AS I32, flags AS U64) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_create_window", I64, CDECL, "STRPTR,I32,I32,U64", title, w, h, flags)
END FUNCTION
SUB DestroyWindow(handle AS I64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_destroy_window", VOID, CDECL, "I64", handle)
END SUB
FUNCTION SetWindowTitle(handle AS I64, title AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_title", I32, CDECL, "I64,STRPTR", handle, title)
END FUNCTION
FUNCTION SetWindowSize(handle AS I64, w AS I32, h AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_size", I32, CDECL, "I64,I32,I32", handle, w, h)
END FUNCTION
FUNCTION GetWindowWidth(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_width", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION GetWindowHeight(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_height", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION ShowWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_show_window", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION HideWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_hide_window", I32, CDECL, "I64", handle)
END FUNCTION

' ---- Renderer ----
FUNCTION CreateRenderer(windowHandle AS I64, name AS STRING) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_create_renderer", I64, CDECL, "I64,STRPTR", windowHandle, name)
END FUNCTION
SUB DestroyRenderer(handle AS I64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_destroy_renderer", VOID, CDECL, "I64", handle)
END SUB
FUNCTION SetRenderDrawColor(handle AS I64, r AS I32, g AS I32, b AS I32, a AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_draw_color", I32, CDECL, "I64,I32,I32,I32,I32", handle, r, g, b, a)
END FUNCTION
FUNCTION RenderClear(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_clear", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION RenderPresent(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_present", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION RenderFillRect(handle AS I64, x AS F64, y AS F64, w AS F64, h AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_fill_rect", I32, CDECL, "I64,F64,F64,F64,F64", handle, x, y, w, h)
END FUNCTION
FUNCTION RenderRect(handle AS I64, x AS F64, y AS F64, w AS F64, h AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_rect", I32, CDECL, "I64,F64,F64,F64,F64", handle, x, y, w, h)
END FUNCTION
FUNCTION RenderLine(handle AS I64, x1 AS F64, y1 AS F64, x2 AS F64, y2 AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_line", I32, CDECL, "I64,F64,F64,F64,F64", handle, x1, y1, x2, y2)
END FUNCTION
FUNCTION RenderPoint(handle AS I64, x AS F64, y AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_point", I32, CDECL, "I64,F64,F64", handle, x, y)
END FUNCTION

' ---- Events / input ----
SUB PumpEvents()
    CALL(DLL, "uxsdl3.dll", "uxsdl3_pump_events", VOID, CDECL)
END SUB
FUNCTION ShouldQuit() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_should_quit", I32, CDECL)
END FUNCTION
FUNCTION KeyDown(scancode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_key_down", I32, CDECL, "I32", scancode)
END FUNCTION
FUNCTION GetMouseX() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_mouse_x", I32, CDECL)
END FUNCTION
FUNCTION GetMouseY() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_mouse_y", I32, CDECL)
END FUNCTION
FUNCTION MouseButtonDown(button AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_mouse_button_down", I32, CDECL, "I32", button)
END FUNCTION

' ---- Timing ----
FUNCTION GetTicks() AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_ticks", I64, CDECL)
END FUNCTION
SUB Delay(ms AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_delay", VOID, CDECL, "I32", ms)
END SUB

' ---- Texture (BMP-backed; SDL3 core ships no PNG/JPEG decoder) ----
FUNCTION LoadTexture(rendererHandle AS I64, bmpPath AS STRING) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_load_texture", I64, CDECL, "I64,STRPTR", rendererHandle, bmpPath)
END FUNCTION
SUB DestroyTexture(handle AS I64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_destroy_texture", VOID, CDECL, "I64", handle)
END SUB
FUNCTION GetTextureWidth(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_texture_width", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION GetTextureHeight(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_texture_height", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION RenderTexture(rendererHandle AS I64, textureHandle AS I64, x AS F64, y AS F64, w AS F64, h AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_texture", I32, CDECL, "I64,I64,F64,F64,F64,F64", rendererHandle, textureHandle, x, y, w, h)
END FUNCTION

' ---- Events (extended) ----
FUNCTION WindowResized() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_resized", I32, CDECL)
END FUNCTION
FUNCTION GetMouseWheelY() AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_mouse_wheel_y", F64, CDECL)
END FUNCTION

' ---- Audio: one-shot WAV sounds ----
' Each loaded sound owns its own playback stream on the default output device;
' Play() re-triggers the same sound and can be called again before it finishes.
FUNCTION LoadSound(wavPath AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_load", I32, CDECL, "STRPTR", wavPath)
END FUNCTION
SUB PlaySound(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_play", VOID, CDECL, "I32", handle)
END SUB
SUB StopSound(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_stop", VOID, CDECL, "I32", handle)
END SUB
SUB UnloadSound(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_unload", VOID, CDECL, "I32", handle)
END SUB

' ---- Clipboard (Init INIT_VIDEO first) ----
FUNCTION SetClipboardText(txt AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_clipboard_text", I32, CDECL, "STRPTR", txt)
END FUNCTION
FUNCTION GetClipboardText() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_clipboard_text", STRPTR, CDECL)
END FUNCTION
FUNCTION HasClipboardText() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_has_clipboard_text", I32, CDECL)
END FUNCTION

' ---- Text input (needs a window; typed text arrives through PumpEvents) ----
FUNCTION StartTextInput(winHandle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_start_text_input", I32, CDECL, "I64", winHandle)
END FUNCTION
FUNCTION StopTextInput(winHandle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_stop_text_input", I32, CDECL, "I64", winHandle)
END FUNCTION
FUNCTION TextInputActive(winHandle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_text_input_active", I32, CDECL, "I64", winHandle)
END FUNCTION
' Rectangle the IME candidate list should avoid (window coordinates) and the cursor offset inside it.
FUNCTION SetTextInputArea(winHandle AS I64, x AS I32, y AS I32, w AS I32, h AS I32, cursor AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_text_input_area", I32, CDECL, "I64,I32,I32,I32,I32,I32", winHandle, x, y, w, h, cursor)
END FUNCTION
' UTF-8 text typed since the previous call (the internal buffer, 1023 bytes, is emptied).
FUNCTION TakeTextInput() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_take_text_input", STRPTR, CDECL)
END FUNCTION
' Queues synthetic typed text; PumpEvents delivers it exactly like real typing (input injection / tests).
FUNCTION PushTextInput(txt AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_text_input", I32, CDECL, "STRPTR", txt)
END FUNCTION
FUNCTION GetScancodeName(scancode AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_scancode_name", STRPTR, CDECL, "I32", scancode)
END FUNCTION
' SDL_Keymod bit set (SDL3/SDL_keycode.h: SDL_KMOD_*).
FUNCTION GetModState() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_mod_state", I32, CDECL)
END FUNCTION

' ---- Joystick / gamepad (Init INIT_JOYSTICK or INIT_GAMEPAD; state refreshes in PumpEvents) ----
' Enumeration returns SDL instance IDs (never 0) for OpenJoystick/OpenGamepad. Handles are 1..15, 0 = failure.
CONST GAMEPAD_BUTTON_SOUTH = 0
CONST GAMEPAD_BUTTON_EAST = 1
CONST GAMEPAD_BUTTON_WEST = 2
CONST GAMEPAD_BUTTON_NORTH = 3
CONST GAMEPAD_BUTTON_BACK = 4
CONST GAMEPAD_BUTTON_GUIDE = 5
CONST GAMEPAD_BUTTON_START = 6
CONST GAMEPAD_BUTTON_LEFT_STICK = 7
CONST GAMEPAD_BUTTON_RIGHT_STICK = 8
CONST GAMEPAD_BUTTON_LEFT_SHOULDER = 9
CONST GAMEPAD_BUTTON_RIGHT_SHOULDER = 10
CONST GAMEPAD_BUTTON_DPAD_UP = 11
CONST GAMEPAD_BUTTON_DPAD_DOWN = 12
CONST GAMEPAD_BUTTON_DPAD_LEFT = 13
CONST GAMEPAD_BUTTON_DPAD_RIGHT = 14
CONST GAMEPAD_AXIS_LEFTX = 0
CONST GAMEPAD_AXIS_LEFTY = 1
CONST GAMEPAD_AXIS_RIGHTX = 2
CONST GAMEPAD_AXIS_RIGHTY = 3
CONST GAMEPAD_AXIS_LEFT_TRIGGER = 4
CONST GAMEPAD_AXIS_RIGHT_TRIGGER = 5
CONST HAT_CENTERED = 0
CONST HAT_UP = 1
CONST HAT_RIGHT = 2
CONST HAT_DOWN = 4
CONST HAT_LEFT = 8

FUNCTION JoystickCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_count", I32, CDECL)
END FUNCTION
FUNCTION JoystickIdAt(idx AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_id_at", I32, CDECL, "I32", idx)
END FUNCTION
FUNCTION OpenJoystick(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_open", I32, CDECL, "I32", instanceId)
END FUNCTION
SUB CloseJoystick(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_close", VOID, CDECL, "I32", handle)
END SUB
FUNCTION JoystickConnected(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_connected", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickName(handle AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_name", STRPTR, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickNumAxes(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_num_axes", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickNumButtons(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_num_buttons", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickNumHats(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_num_hats", I32, CDECL, "I32", handle)
END FUNCTION
' Raw axis value -32768..32767.
FUNCTION JoystickAxis(handle AS I32, axis AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_axis", I32, CDECL, "I32,I32", handle, axis)
END FUNCTION
FUNCTION JoystickButton(handle AS I32, button AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_button", I32, CDECL, "I32,I32", handle, button)
END FUNCTION
' HAT_* bit set.
FUNCTION JoystickHat(handle AS I32, hat AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_hat", I32, CDECL, "I32,I32", handle, hat)
END FUNCTION

FUNCTION GamepadCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_count", I32, CDECL)
END FUNCTION
FUNCTION GamepadIdAt(idx AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_id_at", I32, CDECL, "I32", idx)
END FUNCTION
FUNCTION IsGamepad(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_is_gamepad", I32, CDECL, "I32", instanceId)
END FUNCTION
FUNCTION OpenGamepad(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_open", I32, CDECL, "I32", instanceId)
END FUNCTION
SUB CloseGamepad(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_close", VOID, CDECL, "I32", handle)
END SUB
FUNCTION GamepadConnected(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_connected", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadInstanceId(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_instance_id", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadName(handle AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_name", STRPTR, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadVendor(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_vendor", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadProduct(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_product", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadButton(handle AS I32, button AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_button", I32, CDECL, "I32,I32", handle, button)
END FUNCTION
' Raw axis value -32768..32767 (triggers 0..32767).
FUNCTION GamepadAxis(handle AS I32, axis AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_axis", I32, CDECL, "I32,I32", handle, axis)
END FUNCTION
' Axis normalized to -1.0 .. 1.0 (triggers 0.0 .. 1.0).
FUNCTION GamepadAxisNorm(handle AS I32, axis AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_axis_norm", F64, CDECL, "I32,I32", handle, axis)
END FUNCTION
' low/high motor strength 0..65535 for ms milliseconds; returns 0 when the device cannot rumble.
FUNCTION GamepadRumble(handle AS I32, low AS I32, high AS I32, ms AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_rumble", I32, CDECL, "I32,I32,I32,I32", handle, low, high, ms)
END FUNCTION

' ---- Virtual joystick / gamepad: a device whose inputs the program supplies (input injection, replay, tests) ----
' Attach returns the SDL instance ID (0 = failure); it shows up in the enumerations above and is opened like real hardware.
FUNCTION AttachVirtualJoystick(axes AS I32, buttons AS I32, hats AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_virtual_joystick_attach", I32, CDECL, "I32,I32,I32", axes, buttons, hats)
END FUNCTION
FUNCTION AttachVirtualGamepad() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_virtual_gamepad_attach", I32, CDECL)
END FUNCTION
FUNCTION DetachVirtual(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_virtual_detach", I32, CDECL, "I32", instanceId)
END FUNCTION
FUNCTION SetVirtualJoystickAxis(handle AS I32, axis AS I32, value AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_set_virtual_axis", I32, CDECL, "I32,I32,I32", handle, axis, value)
END FUNCTION
FUNCTION SetVirtualJoystickButton(handle AS I32, button AS I32, down AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_set_virtual_button", I32, CDECL, "I32,I32,I32", handle, button, down)
END FUNCTION
FUNCTION SetVirtualJoystickHat(handle AS I32, hat AS I32, value AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_set_virtual_hat", I32, CDECL, "I32,I32,I32", handle, hat, value)
END FUNCTION
FUNCTION SetVirtualGamepadAxis(handle AS I32, axis AS I32, value AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_set_virtual_axis", I32, CDECL, "I32,I32,I32", handle, axis, value)
END FUNCTION
FUNCTION SetVirtualGamepadButton(handle AS I32, button AS I32, down AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_set_virtual_button", I32, CDECL, "I32,I32,I32", handle, button, down)
END FUNCTION


' ================================================================================================
' Full SDL3 surface (video/window, events, mouse/keyboard, renderer, audio, gamepad, filesystem, system).
' Grouped getters take a 'which' selector (PART_* / COMP_* or the numbers documented on each function).
' ================================================================================================
' ---- Window flags (CreateWindow flags, GetWindowFlags, HasWindowFlag) ----
CONST WINDOW_FULLSCREEN = 1
CONST WINDOW_HIDDEN = 8
CONST WINDOW_BORDERLESS = 16
CONST WINDOW_RESIZABLE = 32
CONST WINDOW_MINIMIZED = 64
CONST WINDOW_MAXIMIZED = 128
CONST WINDOW_MOUSE_GRABBED = 256
CONST WINDOW_INPUT_FOCUS = 512
CONST WINDOW_MOUSE_FOCUS = 1024
CONST WINDOW_HIGH_PIXEL_DENSITY = 8192
CONST WINDOW_MOUSE_CAPTURE = 16384
CONST WINDOW_MOUSE_RELATIVE_MODE = 32768
CONST WINDOW_ALWAYS_ON_TOP = 65536
CONST WINDOW_UTILITY = 131072
CONST WINDOW_KEYBOARD_GRABBED = 1048576
CONST WINDOW_TRANSPARENT = 1073741824
CONST WINDOW_NOT_FOCUSABLE = 2147483648

' ---- Bits returned by WindowEvents() (window events seen by the last PumpEvents) ----
CONST WINDOWEVT_FOCUS_GAINED = 1
CONST WINDOWEVT_FOCUS_LOST = 2
CONST WINDOWEVT_MINIMIZED = 4
CONST WINDOWEVT_MAXIMIZED = 8
CONST WINDOWEVT_RESTORED = 16
CONST WINDOWEVT_MOVED = 32
CONST WINDOWEVT_CLOSE_REQUESTED = 64
CONST WINDOWEVT_EXPOSED = 128
CONST WINDOWEVT_MOUSE_ENTER = 256
CONST WINDOWEVT_MOUSE_LEAVE = 512
CONST WINDOWEVT_SHOWN = 1024
CONST WINDOWEVT_HIDDEN = 2048
CONST WINDOWEVT_RESIZED = 4096

' ---- Selectors for the "which" parameter of grouped getters ----
CONST PART_X = 0
CONST PART_Y = 1
CONST PART_W = 2
CONST PART_H = 3
CONST COMP_R = 0
CONST COMP_G = 1
CONST COMP_B = 2
CONST COMP_A = 3

' ---- TakeDeviceEvents(which) ----
CONST DEVICE_JOYSTICK_ADDED = 0
CONST DEVICE_JOYSTICK_REMOVED = 1
CONST DEVICE_GAMEPAD_ADDED = 2
CONST DEVICE_GAMEPAD_REMOVED = 3

' ---- Mouse buttons ----
CONST MOUSE_LEFT = 1
CONST MOUSE_MIDDLE = 2
CONST MOUSE_RIGHT = 3
CONST MOUSE_X1 = 4
CONST MOUSE_X2 = 5

' ---- System cursors (SetSystemCursor) ----
CONST CURSOR_DEFAULT = 0
CONST CURSOR_TEXT = 1
CONST CURSOR_WAIT = 2
CONST CURSOR_CROSSHAIR = 3
CONST CURSOR_PROGRESS = 4
CONST CURSOR_NWSE_RESIZE = 5
CONST CURSOR_NESW_RESIZE = 6
CONST CURSOR_EW_RESIZE = 7
CONST CURSOR_NS_RESIZE = 8
CONST CURSOR_MOVE = 9
CONST CURSOR_NOT_ALLOWED = 10
CONST CURSOR_POINTER = 11

' ---- Renderer: blend modes, texture access, scale modes, logical presentation, flip ----
CONST BLEND_NONE = 0
CONST BLEND_BLEND = 1
CONST BLEND_ADD = 2
CONST BLEND_MOD = 4
CONST BLEND_MUL = 8
CONST BLEND_BLEND_PREMULTIPLIED = 16
CONST BLEND_ADD_PREMULTIPLIED = 32
CONST TEXTUREACCESS_STATIC = 0
CONST TEXTUREACCESS_STREAMING = 1
CONST TEXTUREACCESS_TARGET = 2
CONST SCALEMODE_NEAREST = 0
CONST SCALEMODE_LINEAR = 1
CONST LOGICAL_DISABLED = 0
CONST LOGICAL_STRETCH = 1
CONST LOGICAL_LETTERBOX = 2
CONST LOGICAL_OVERSCAN = 3
CONST LOGICAL_INTEGER_SCALE = 4
CONST FLIP_NONE = 0
CONST FLIP_HORIZONTAL = 1
CONST FLIP_VERTICAL = 2
' RenderTextureRotated: add this to the flip value to rotate around (cx, cy) instead of the center.
CONST ROTATE_AROUND_POINT = 4

' ---- Filesystem: PathType results ----
CONST PATH_NONE = 0
CONST PATH_FILE = 1
CONST PATH_DIRECTORY = 2
CONST PATH_OTHER = 3

' ---- Power (PowerState, GamepadPowerState, JoystickPowerState) ----
CONST POWER_ERROR = -1
CONST POWER_UNKNOWN = 0
CONST POWER_ON_BATTERY = 1
CONST POWER_NO_BATTERY = 2
CONST POWER_CHARGING = 3
CONST POWER_CHARGED = 4

' ---- Gamepad sensors and joystick types ----
CONST SENSOR_ACCEL = 1
CONST SENSOR_GYRO = 2
CONST JOYSTICK_TYPE_UNKNOWN = 0
CONST JOYSTICK_TYPE_GAMEPAD = 1
CONST JOYSTICK_TYPE_WHEEL = 2
CONST JOYSTICK_TYPE_ARCADE_STICK = 3
CONST JOYSTICK_TYPE_FLIGHT_STICK = 4
CONST JOYSTICK_TYPE_DANCE_PAD = 5
CONST JOYSTICK_TYPE_GUITAR = 6
CONST JOYSTICK_TYPE_DRUM_KIT = 7
CONST JOYSTICK_TYPE_ARCADE_PAD = 8
CONST JOYSTICK_TYPE_THROTTLE = 9

' ---- FlashWindow operations ----
CONST FLASH_CANCEL = 0
CONST FLASH_BRIEFLY = 1
CONST FLASH_UNTIL_FOCUSED = 2

SUB ClearQuit()
    CALL(DLL, "uxsdl3.dll", "uxsdl3_clear_quit", VOID, CDECL)
END SUB
' Bit set of window events seen by the last pump: 1 focus gained, 2 focus lost, 4 minimized, 8 maximized,
' 16 restored, 32 moved, 64 close requested, 128 exposed, 256 mouse enter, 512 mouse leave, 1024 shown,
' 2048 hidden, 4096 resized.
FUNCTION WindowEvents() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_events", I32, CDECL)
END FUNCTION
FUNCTION GetMouseWheelX() AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_mouse_wheel_x", F64, CDECL)
END FUNCTION
FUNCTION KeyPressed(scancode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_key_pressed", I32, CDECL, "I32", scancode)
END FUNCTION
FUNCTION KeyReleased(scancode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_key_released", I32, CDECL, "I32", scancode)
END FUNCTION
FUNCTION LastKey() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_last_key", I32, CDECL)
END FUNCTION
FUNCTION MouseButtonPressed(button AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_mouse_button_pressed", I32, CDECL, "I32", button)
END FUNCTION
FUNCTION MouseButtonReleased(button AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_mouse_button_released", I32, CDECL, "I32", button)
END FUNCTION
FUNCTION MouseRelX() AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_mouse_rel_x", F64, CDECL)
END FUNCTION
FUNCTION MouseRelY() AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_mouse_rel_y", F64, CDECL)
END FUNCTION
' Device hot-plug: how many were added/removed since the last read (which: 0 joystick added, 1 joystick removed,
' 2 gamepad added, 3 gamepad removed). Reading clears the counter.
FUNCTION TakeDeviceEvents(which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_take_device_events", I32, CDECL, "I32", which)
END FUNCTION
' Dropped files / text, oldest first.
FUNCTION DropCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_drop_count", I32, CDECL)
END FUNCTION
FUNCTION TakeDrop() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_take_drop", STRPTR, CDECL)
END FUNCTION
' Injects a dropped file path (input injection / tests); it is queued directly (SDL would keep the caller's pointer).
FUNCTION PushDrop(text AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_drop", I32, CDECL, "STRPTR", text)
END FUNCTION
FUNCTION PushQuit() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_quit", I32, CDECL)
END FUNCTION
FUNCTION PushKey(scancode AS I32, down AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_key", I32, CDECL, "I32,I32", scancode, down)
END FUNCTION
FUNCTION PushMouseButton(button AS I32, down AS I32, x AS F64, y AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_mouse_button", I32, CDECL, "I32,I32,F64,F64", button, down, x, y)
END FUNCTION
FUNCTION PushMouseMotion(x AS F64, y AS F64, xrel AS F64, yrel AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_mouse_motion", I32, CDECL, "F64,F64,F64,F64", x, y, xrel, yrel)
END FUNCTION
FUNCTION PushMouseWheel(x AS F64, y AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_push_mouse_wheel", I32, CDECL, "F64,F64", x, y)
END FUNCTION
SUB FlushEvents()
    CALL(DLL, "uxsdl3.dll", "uxsdl3_flush_events", VOID, CDECL)
END SUB
' A generated sine tone (16-bit mono, 44.1 kHz) with a 5 ms fade in/out so it does not click.
' freqHz 20..20000, ms 1..60000, volume 0.0..1.0 (baked into the samples).
FUNCTION CreateTone(freqHz AS I32, ms AS I32, volume AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_create_tone", I32, CDECL, "I32,I32,F64", freqHz, ms, volume)
END FUNCTION
SUB PauseSound(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_pause", VOID, CDECL, "I32", handle)
END SUB
SUB ResumeSound(handle AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_resume", VOID, CDECL, "I32", handle)
END SUB
' Writes a sound (a loaded WAV or a generated tone) as a WAV file; returns 1 on success.
FUNCTION SaveSoundWAV(handle AS I32, path AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_save_wav", I32, CDECL, "I32,STRPTR", handle, path)
END FUNCTION
FUNCTION IsSoundPlaying(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_is_playing", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION IsSoundPaused(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_is_paused", I32, CDECL, "I32", handle)
END FUNCTION
SUB SetSoundLoop(handle AS I32, looping AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_set_loop", VOID, CDECL, "I32,I32", handle, looping)
END SUB
FUNCTION GetSoundLoop(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_get_loop", I32, CDECL, "I32", handle)
END FUNCTION
' Volume 0.0 .. 4.0 (1.0 = as recorded), multiplied by the master volume.
SUB SetSoundVolume(handle AS I32, volume AS F64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_set_volume", VOID, CDECL, "I32,F64", handle, volume)
END SUB
FUNCTION GetSoundVolume(handle AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_get_volume", F64, CDECL, "I32", handle)
END FUNCTION
SUB SetMasterVolume(volume AS F64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_set_master_volume", VOID, CDECL, "F64", volume)
END SUB
FUNCTION GetMasterVolume() AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_master_volume", F64, CDECL)
END FUNCTION
FUNCTION SoundLengthMs(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_length_ms", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION SoundRemainingMs(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_remaining_ms", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION SoundFrequency(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_frequency", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION SoundChannels(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sound_channels", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION AudioDeviceCount(recording AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_audio_device_count", I32, CDECL, "I32", recording)
END FUNCTION
FUNCTION AudioDeviceName(recording AS I32, index AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_audio_device_name", STRPTR, CDECL, "I32,I32", recording, index)
END FUNCTION
FUNCTION AudioDriverCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_audio_driver_count", I32, CDECL)
END FUNCTION
FUNCTION AudioDriverName(index AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_audio_driver_name", STRPTR, CDECL, "I32", index)
END FUNCTION
FUNCTION CurrentAudioDriver() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_current_audio_driver", STRPTR, CDECL)
END FUNCTION
FUNCTION InitSubSystem(flags AS U32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_init_subsystem", I32, CDECL, "U32", U32(flags))
END FUNCTION
SUB QuitSubSystem(flags AS U32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_quit_subsystem", VOID, CDECL, "U32", U32(flags))
END SUB
FUNCTION WasInit(flags AS U32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_was_init", I32, CDECL, "U32", U32(flags))
END FUNCTION
SUB ClearError()
    CALL(DLL, "uxsdl3.dll", "uxsdl3_clear_error", VOID, CDECL)
END SUB
FUNCTION GetPlatform() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_platform", STRPTR, CDECL)
END FUNCTION
FUNCTION SetAppMetadata(name AS STRING, version AS STRING, identifier AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_app_metadata", I32, CDECL, "STRPTR,STRPTR,STRPTR", name, version, identifier)
END FUNCTION
' which: 0 name, 1 version, 2 identifier
FUNCTION GetAppMetadata(which AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_app_metadata", STRPTR, CDECL, "I32", which)
END FUNCTION
FUNCTION SetHint(name AS STRING, value AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_hint", I32, CDECL, "STRPTR,STRPTR", name, value)
END FUNCTION
FUNCTION GetHint(name AS STRING) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_hint", STRPTR, CDECL, "STRPTR", name)
END FUNCTION
FUNCTION DisplayCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_count", I32, CDECL)
END FUNCTION
FUNCTION DisplayIdAt(index AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_id_at", I32, CDECL, "I32", index)
END FUNCTION
FUNCTION PrimaryDisplay() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_primary_display", I32, CDECL)
END FUNCTION
FUNCTION DisplayName(displayId AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_name", STRPTR, CDECL, "I32", displayId)
END FUNCTION
' which: 0 x, 1 y, 2 width, 3 height (0 when the display is unknown)
FUNCTION DisplayBounds(displayId AS I32, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_bounds", I32, CDECL, "I32,I32", displayId, which)
END FUNCTION
FUNCTION DisplayUsableBounds(displayId AS I32, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_usable_bounds", I32, CDECL, "I32,I32", displayId, which)
END FUNCTION
' Desktop display mode. which: 0 width, 1 height, 2 refresh rate x100 (Hz), 3 pixel density x100
FUNCTION DisplayMode(displayId AS I32, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_mode", I32, CDECL, "I32,I32", displayId, which)
END FUNCTION
FUNCTION DisplayContentScale(displayId AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_content_scale", F64, CDECL, "I32", displayId)
END FUNCTION
FUNCTION DisplayOrientation(displayId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_display_orientation", I32, CDECL, "I32", displayId)
END FUNCTION
FUNCTION VideoDriverCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_video_driver_count", I32, CDECL)
END FUNCTION
FUNCTION VideoDriverName(index AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_video_driver_name", STRPTR, CDECL, "I32", index)
END FUNCTION
FUNCTION CurrentVideoDriver() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_current_video_driver", STRPTR, CDECL)
END FUNCTION
FUNCTION ScreensaverEnabled() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_screensaver_enabled", I32, CDECL)
END FUNCTION
FUNCTION SetScreensaver(enabled AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_screensaver", I32, CDECL, "I32", enabled)
END FUNCTION
FUNCTION SystemTheme() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_system_theme", I32, CDECL)
END FUNCTION
FUNCTION GetWindowTitle(handle AS I64) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_title", STRPTR, CDECL, "I64", handle)
END FUNCTION
' which: 0 width, 1 height in real pixels (differs from the window size on high-DPI displays)
FUNCTION GetWindowPixelSize(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_pixel_size", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION SetWindowPosition(handle AS I64, x AS I32, y AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_position", I32, CDECL, "I64,I32,I32", handle, x, y)
END FUNCTION
' which: 0 x, 1 y
FUNCTION GetWindowPosition(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_position", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION SetWindowMinSize(handle AS I64, w AS I32, h AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_min_size", I32, CDECL, "I64,I32,I32", handle, w, h)
END FUNCTION
FUNCTION SetWindowMaxSize(handle AS I64, w AS I32, h AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_max_size", I32, CDECL, "I64,I32,I32", handle, w, h)
END FUNCTION
' which: 0 width, 1 height (0 = no limit)
FUNCTION GetWindowMinSize(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_min_size", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION GetWindowMaxSize(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_max_size", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION SetWindowFullscreen(handle AS I64, fullscreen AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_fullscreen", I32, CDECL, "I64,I32", handle, fullscreen)
END FUNCTION
FUNCTION GetWindowFlags(handle AS I64) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_flags", I64, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetWindowBordered(handle AS I64, bordered AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_bordered", I32, CDECL, "I64,I32", handle, bordered)
END FUNCTION
FUNCTION SetWindowResizable(handle AS I64, resizable AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_resizable", I32, CDECL, "I64,I32", handle, resizable)
END FUNCTION
FUNCTION SetWindowAlwaysOnTop(handle AS I64, onTop AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_always_on_top", I32, CDECL, "I64,I32", handle, onTop)
END FUNCTION
FUNCTION SetWindowFocusable(handle AS I64, focusable AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_focusable", I32, CDECL, "I64,I32", handle, focusable)
END FUNCTION
FUNCTION MinimizeWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_minimize_window", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION MaximizeWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_maximize_window", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION RestoreWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_restore_window", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION RaiseWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_raise_window", I32, CDECL, "I64", handle)
END FUNCTION
' Waits until pending window changes (position, size, state) have been applied; returns 1 when they were.
FUNCTION SyncWindow(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_sync_window", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetWindowOpacity(handle AS I64, opacity AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_opacity", I32, CDECL, "I64,F64", handle, opacity)
END FUNCTION
FUNCTION GetWindowOpacity(handle AS I64) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_opacity", F64, CDECL, "I64", handle)
END FUNCTION
FUNCTION WindowId(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_id", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION WindowFromId(id AS I32) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_from_id", I64, CDECL, "I32", id)
END FUNCTION
FUNCTION WindowDisplay(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_display", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION WindowDisplayScale(handle AS I64) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_display_scale", F64, CDECL, "I64", handle)
END FUNCTION
FUNCTION WindowPixelDensity(handle AS I64) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_window_pixel_density", F64, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetWindowMouseGrab(handle AS I64, grabbed AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_mouse_grab", I32, CDECL, "I64,I32", handle, grabbed)
END FUNCTION
FUNCTION GetWindowMouseGrab(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_mouse_grab", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetWindowKeyboardGrab(handle AS I64, grabbed AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_keyboard_grab", I32, CDECL, "I64,I32", handle, grabbed)
END FUNCTION
FUNCTION GetWindowKeyboardGrab(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_keyboard_grab", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetWindowRelativeMouse(handle AS I64, enabled AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_relative_mouse", I32, CDECL, "I64,I32", handle, enabled)
END FUNCTION
FUNCTION GetWindowRelativeMouse(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_window_relative_mouse", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetWindowIconBMP(handle AS I64, bmpPath AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_window_icon_bmp", I32, CDECL, "I64,STRPTR", handle, bmpPath)
END FUNCTION
' operation: 0 cancel, 1 briefly, 2 until focused
FUNCTION FlashWindow(handle AS I64, operation AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_flash_window", I32, CDECL, "I64,I32", handle, operation)
END FUNCTION
FUNCTION ShowCursor() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_show_cursor", I32, CDECL)
END FUNCTION
FUNCTION HideCursor() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_hide_cursor", I32, CDECL)
END FUNCTION
FUNCTION CursorVisible() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_cursor_visible", I32, CDECL)
END FUNCTION
' Switches to a system cursor (created once, reused). id: see CURSOR_* in uxsdl3.bas.
FUNCTION SetSystemCursor(id AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_system_cursor", I32, CDECL, "I32", id)
END FUNCTION
FUNCTION WarpMouseInWindow(handle AS I64, x AS F64, y AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_warp_mouse_in_window", I32, CDECL, "I64,F64,F64", handle, x, y)
END FUNCTION
FUNCTION WarpMouseGlobal(x AS F64, y AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_warp_mouse_global", I32, CDECL, "F64,F64", x, y)
END FUNCTION
FUNCTION CaptureMouse(enabled AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_capture_mouse", I32, CDECL, "I32", enabled)
END FUNCTION
' which: 0 x, 1 y (desktop coordinates)
FUNCTION GlobalMouse(which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_global_mouse", I32, CDECL, "I32", which)
END FUNCTION
FUNCTION HasMouse() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_has_mouse", I32, CDECL)
END FUNCTION
FUNCTION HasKeyboard() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_has_keyboard", I32, CDECL)
END FUNCTION
FUNCTION MouseCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_mouse_count", I32, CDECL)
END FUNCTION
FUNCTION KeyboardCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_keyboard_count", I32, CDECL)
END FUNCTION
FUNCTION ScancodeFromName(name AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_scancode_from_name", I32, CDECL, "STRPTR", name)
END FUNCTION
FUNCTION KeyFromScancode(scancode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_key_from_scancode", I32, CDECL, "I32", scancode)
END FUNCTION
FUNCTION ScancodeFromKey(keycode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_scancode_from_key", I32, CDECL, "I32", keycode)
END FUNCTION
FUNCTION KeyName(keycode AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_key_name", STRPTR, CDECL, "I32", keycode)
END FUNCTION
FUNCTION HasScreenKeyboard() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_has_screen_keyboard", I32, CDECL)
END FUNCTION
SUB SetModState(mods AS I32)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_set_mod_state", VOID, CDECL, "I32", mods)
END SUB
FUNCTION RendererName(handle AS I64) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_renderer_name", STRPTR, CDECL, "I64", handle)
END FUNCTION
' which: 0 width, 1 height of the current render output (or target texture) in pixels
FUNCTION RenderOutputSize(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_output_size", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
' which: 0 red, 1 green, 2 blue, 3 alpha of the current draw color
FUNCTION GetRenderDrawColor(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_draw_color", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION SetRenderDrawBlendMode(handle AS I64, mode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_draw_blend_mode", I32, CDECL, "I64,I32", handle, mode)
END FUNCTION
' Returns the blend mode, or -1 for an invalid renderer.
FUNCTION GetRenderDrawBlendMode(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_draw_blend_mode", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetRenderViewport(handle AS I64, x AS I32, y AS I32, w AS I32, h AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_viewport", I32, CDECL, "I64,I32,I32,I32,I32", handle, x, y, w, h)
END FUNCTION
FUNCTION ResetRenderViewport(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_reset_render_viewport", I32, CDECL, "I64", handle)
END FUNCTION
' which: 0 x, 1 y, 2 width, 3 height
FUNCTION GetRenderViewport(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_viewport", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION SetRenderClipRect(handle AS I64, x AS I32, y AS I32, w AS I32, h AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_clip_rect", I32, CDECL, "I64,I32,I32,I32,I32", handle, x, y, w, h)
END FUNCTION
FUNCTION DisableRenderClip(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_disable_render_clip", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION RenderClipEnabled(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_clip_enabled", I32, CDECL, "I64", handle)
END FUNCTION
' which: 0 x, 1 y, 2 width, 3 height
FUNCTION GetRenderClipRect(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_clip_rect", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION SetRenderScale(handle AS I64, sx AS F64, sy AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_scale", I32, CDECL, "I64,F64,F64", handle, sx, sy)
END FUNCTION
' which: 0 x scale, 1 y scale
FUNCTION GetRenderScale(handle AS I64, which AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_scale", F64, CDECL, "I64,I32", handle, which)
END FUNCTION
' Renders at a fixed logical size and lets SDL scale it to the output. mode: see LOGICAL_* in uxsdl3.bas.
FUNCTION SetRenderLogicalPresentation(handle AS I64, w AS I32, h AS I32, mode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_logical_presentation", I32, CDECL, "I64,I32,I32,I32", handle, w, h, mode)
END FUNCTION
' Returns the logical width (which 0) or height (which 1); 0 when no logical size is set.
FUNCTION GetRenderLogicalSize(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_logical_size", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION GetRenderLogicalMode(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_logical_mode", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION SetRenderVSync(handle AS I64, vsync AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_vsync", I32, CDECL, "I64,I32", handle, vsync)
END FUNCTION
' Returns the vsync interval, or -2 when it cannot be read.
FUNCTION GetRenderVSync(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_render_vsync", I32, CDECL, "I64", handle)
END FUNCTION
' Window pixel position -> render (logical) coordinates and back. which: 0 x, 1 y.
FUNCTION RenderCoordsFromWindow(handle AS I64, wx AS F64, wy AS F64, which AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_coords_from_window", F64, CDECL, "I64,F64,F64,I32", handle, wx, wy, which)
END FUNCTION
FUNCTION RenderCoordsToWindow(handle AS I64, x AS F64, y AS F64, which AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_coords_to_window", F64, CDECL, "I64,F64,F64,I32", handle, x, y, which)
END FUNCTION
' The pixel at (x, y) of the current render target, packed RGBA; 0 when outside or on error.
FUNCTION RenderReadPixel(handle AS I64, x AS I32, y AS I32) AS U32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_read_pixel", U32, CDECL, "I64,I32,I32", handle, x, y)
END FUNCTION
' Saves the whole current render target as a BMP file (a screenshot).
FUNCTION RenderSaveBMP(handle AS I64, path AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_save_bmp", I32, CDECL, "I64,STRPTR", handle, path)
END FUNCTION
' Built-in 8x8 debug font (ASCII); scale with uxsdl3_set_render_scale.
FUNCTION RenderDebugText(handle AS I64, x AS F64, y AS F64, text AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_debug_text", I32, CDECL, "I64,F64,F64,STRPTR", handle, x, y, text)
END FUNCTION
' Renders into a texture created with TEXTUREACCESS_TARGET; texture 0 goes back to the window.
FUNCTION SetRenderTarget(handle AS I64, texture AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_set_render_target", I32, CDECL, "I64,I64", handle, texture)
END FUNCTION
' A blank RGBA texture. access: 0 static, 1 streaming, 2 render target.
FUNCTION CreateTexture(rendererHandle AS I64, w AS I32, h AS I32, access AS I32) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_create_texture", I64, CDECL, "I64,I32,I32,I32", rendererHandle, w, h, access)
END FUNCTION
' Fills every pixel with one packed RGBA color (static or streaming textures).
FUNCTION TextureFill(handle AS I64, rgba AS U32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_fill", I32, CDECL, "I64,U32", handle, U32(rgba))
END FUNCTION
' Writes one pixel (static or streaming textures).
FUNCTION TextureSetPixel(handle AS I64, x AS I32, y AS I32, rgba AS U32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_set_pixel", I32, CDECL, "I64,I32,I32,U32", handle, x, y, U32(rgba))
END FUNCTION
FUNCTION TextureSetColorMod(handle AS I64, r AS I32, g AS I32, b AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_set_color_mod", I32, CDECL, "I64,I32,I32,I32", handle, r, g, b)
END FUNCTION
' which: 0 red, 1 green, 2 blue
FUNCTION TextureGetColorMod(handle AS I64, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_get_color_mod", I32, CDECL, "I64,I32", handle, which)
END FUNCTION
FUNCTION TextureSetAlphaMod(handle AS I64, a AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_set_alpha_mod", I32, CDECL, "I64,I32", handle, a)
END FUNCTION
FUNCTION TextureGetAlphaMod(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_get_alpha_mod", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION TextureSetBlendMode(handle AS I64, mode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_set_blend_mode", I32, CDECL, "I64,I32", handle, mode)
END FUNCTION
' Returns the blend mode, or -1 for an invalid texture.
FUNCTION TextureGetBlendMode(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_get_blend_mode", I32, CDECL, "I64", handle)
END FUNCTION
FUNCTION TextureSetScaleMode(handle AS I64, mode AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_set_scale_mode", I32, CDECL, "I64,I32", handle, mode)
END FUNCTION
' Returns the scale mode, or -1 for an invalid texture.
FUNCTION TextureGetScaleMode(handle AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_texture_get_scale_mode", I32, CDECL, "I64", handle)
END FUNCTION
' A part of the texture (source rectangle) drawn into a destination rectangle.
FUNCTION RenderTextureRect(rendererHandle AS I64, textureHandle AS I64, sx AS F64, sy AS F64, sw AS F64, sh AS F64, dx AS F64, dy AS F64, dw AS F64, dh AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_texture_rect", I32, CDECL, "I64,I64,F64,F64,F64,F64,F64,F64,F64,F64", rendererHandle, textureHandle, sx, sy, sw, sh, dx, dy, dw, dh)
END FUNCTION
' Whole texture, rotated by angle degrees (clockwise) and optionally flipped.
' flipAndCenter: bits 0-1 = flip (0 none, 1 horizontal, 2 vertical); bit 2 (4) = rotate around (cx, cy)
' relative to the destination rectangle's top-left corner instead of around its center.
FUNCTION RenderTextureRotated(rendererHandle AS I64, textureHandle AS I64, dx AS F64, dy AS F64, dw AS F64, dh AS F64, angle AS F64, cx AS F64, cy AS F64, flipAndCenter AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_texture_rotated", I32, CDECL, "I64,I64,F64,F64,F64,F64,F64,F64,F64,I32", rendererHandle, textureHandle, dx, dy, dw, dh, angle, cx, cy, flipAndCenter)
END FUNCTION
' Sprite sheet: frame number frameIndex (left to right, top to bottom) of frameW x frameH cells.
FUNCTION RenderTextureFrame(rendererHandle AS I64, textureHandle AS I64, frameW AS I32, frameH AS I32, frameIndex AS I32, dx AS F64, dy AS F64, dw AS F64, dh AS F64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_render_texture_frame", I32, CDECL, "I64,I64,I32,I32,I32,F64,F64,F64,F64", rendererHandle, textureHandle, frameW, frameH, frameIndex, dx, dy, dw, dh)
END FUNCTION
FUNCTION GetTicksNS() AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_get_ticks_ns", I64, CDECL)
END FUNCTION
FUNCTION PerfCounter() AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_perf_counter", I64, CDECL)
END FUNCTION
FUNCTION PerfFrequency() AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_perf_frequency", I64, CDECL)
END FUNCTION
SUB DelayNS(ns AS I64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_delay_ns", VOID, CDECL, "I64", ns)
END SUB
SUB DelayPreciseNS(ns AS I64)
    CALL(DLL, "uxsdl3.dll", "uxsdl3_delay_precise_ns", VOID, CDECL, "I64", ns)
END SUB
' Wall clock: nanoseconds since 1970-01-01 UTC, and its calendar parts.
' which: 0 year, 1 month, 2 day, 3 hour, 4 minute, 5 second, 6 nanosecond, 7 day of week (0 = Sunday),
' 8 offset from UTC in seconds (localTime <> 0 converts to the local time zone).
FUNCTION CurrentTimeNS() AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_current_time_ns", I64, CDECL)
END FUNCTION
FUNCTION DatePart(ns AS I64, localTime AS I32, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_date_part", I32, CDECL, "I64,I32,I32", ns, localTime, which)
END FUNCTION
' Days in a month (1-12) of a year, leap years included; -1 for an invalid month.
FUNCTION DaysInMonth(year AS I32, month AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_days_in_month", I32, CDECL, "I32,I32", year, month)
END FUNCTION
FUNCTION DayOfYear(year AS I32, month AS I32, day AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_day_of_year", I32, CDECL, "I32,I32,I32", year, month, day)
END FUNCTION
FUNCTION BasePath() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_base_path", STRPTR, CDECL)
END FUNCTION
' Per-user writable folder for an application (created when missing), ending in a path separator.
FUNCTION PrefPath(org AS STRING, app AS STRING) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_pref_path", STRPTR, CDECL, "STRPTR,STRPTR", org, app)
END FUNCTION
FUNCTION CurrentDirectory() AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_current_directory", STRPTR, CDECL)
END FUNCTION
FUNCTION CreateDirectory(path AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_create_directory", I32, CDECL, "STRPTR", path)
END FUNCTION
' 0 = does not exist, 1 = file, 2 = directory, 3 = other
FUNCTION PathType(path AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_path_type", I32, CDECL, "STRPTR", path)
END FUNCTION
FUNCTION PathSize(path AS STRING) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_path_size", I64, CDECL, "STRPTR", path)
END FUNCTION
' Last modification time (nanoseconds since 1970, see uxsdl3_date_part); 0 when unknown.
FUNCTION PathModifyTime(path AS STRING) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_path_modify_time", I64, CDECL, "STRPTR", path)
END FUNCTION
' Removes a file or an EMPTY directory (1 also when the path does not exist; 0 for a directory that still has entries).
FUNCTION RemovePath(path AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_remove_path", I32, CDECL, "STRPTR", path)
END FUNCTION
FUNCTION RenamePath(oldPath AS STRING, newPath AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_rename_path", I32, CDECL, "STRPTR,STRPTR", oldPath, newPath)
END FUNCTION
FUNCTION CopyFile(oldPath AS STRING, newPath AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_copy_file", I32, CDECL, "STRPTR,STRPTR", oldPath, newPath)
END FUNCTION
' Entries of a directory whose names match a pattern ('*' and '?'), in the folder itself; an EMPTY pattern lists everything
' below the folder, recursively (sub-folder entries come as "sub\name"). The count is returned; read the names with
' uxsdl3_list_item. A new call replaces the previous list; -1 on error (for example a missing folder).
FUNCTION ListDirectory(path AS STRING, pattern AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_list_directory", I32, CDECL, "STRPTR,STRPTR", path, pattern)
END FUNCTION
FUNCTION ListItem(index AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_list_item", STRPTR, CDECL, "I32", index)
END FUNCTION
FUNCTION CPUCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_cpu_count", I32, CDECL)
END FUNCTION
FUNCTION SystemRAMMB() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_system_ram_mb", I32, CDECL)
END FUNCTION
FUNCTION CPUCacheLineSize() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_cpu_cache_line_size", I32, CDECL)
END FUNCTION
' which: 0 MMX, 1 SSE, 2 SSE2, 3 SSE3, 4 SSE4.1, 5 SSE4.2, 6 AVX, 7 AVX2, 8 AVX-512F, 9 NEON, 10 AltiVec, 11 LSX, 12 LASX
FUNCTION CPUFeature(which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_cpu_feature", I32, CDECL, "I32", which)
END FUNCTION
FUNCTION IsTablet() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_is_tablet", I32, CDECL)
END FUNCTION
FUNCTION IsTV() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_is_tv", I32, CDECL)
END FUNCTION
' Power state: 0 unknown/error(-1), see POWER_* in uxsdl3.bas; seconds/percent are -1 when unknown.
FUNCTION PowerState() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_power_state", I32, CDECL)
END FUNCTION
FUNCTION PowerSeconds() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_power_seconds", I32, CDECL)
END FUNCTION
FUNCTION PowerPercent() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_power_percent", I32, CDECL)
END FUNCTION
FUNCTION LocaleCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_locale_count", I32, CDECL)
END FUNCTION
FUNCTION LocaleLanguage(index AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_locale_language", STRPTR, CDECL, "I32", index)
END FUNCTION
FUNCTION LocaleCountry(index AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_locale_country", STRPTR, CDECL, "I32", index)
END FUNCTION
FUNCTION TouchDeviceCount() AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_touch_device_count", I32, CDECL)
END FUNCTION
FUNCTION TouchDeviceIdAt(index AS I32) AS I64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_touch_device_id_at", I64, CDECL, "I32", index)
END FUNCTION
FUNCTION TouchDeviceName(id AS I64) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_touch_device_name", STRPTR, CDECL, "I64", id)
END FUNCTION
' -1 invalid, 0 touch screen (direct), 1 trackpad (absolute), 2 trackpad (relative)
FUNCTION TouchDeviceType(id AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_touch_device_type", I32, CDECL, "I64", id)
END FUNCTION
FUNCTION TouchFingerCount(id AS I64) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_touch_finger_count", I32, CDECL, "I64", id)
END FUNCTION
' which: 0 x, 1 y (both 0..1 across the device), 2 pressure 0..1
FUNCTION TouchFinger(id AS I64, index AS I32, which AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_touch_finger", F64, CDECL, "I64,I32,I32", id, index, which)
END FUNCTION
FUNCTION JoystickNameForId(instanceId AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_name_for_id", STRPTR, CDECL, "I32", instanceId)
END FUNCTION
FUNCTION GamepadNameForId(instanceId AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_name_for_id", STRPTR, CDECL, "I32", instanceId)
END FUNCTION
FUNCTION JoystickVendorForId(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_vendor_for_id", I32, CDECL, "I32", instanceId)
END FUNCTION
FUNCTION JoystickProductForId(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_product_for_id", I32, CDECL, "I32", instanceId)
END FUNCTION
' 0 unknown, 1 gamepad, 2 wheel, 3 arcade stick, 4 flight stick, 5 dance pad, 6 guitar, 7 drum kit, 8 arcade pad, 9 throttle
FUNCTION JoystickTypeForId(instanceId AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_type_for_id", I32, CDECL, "I32", instanceId)
END FUNCTION
FUNCTION JoystickInstanceId(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_instance_id", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickVendor(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_vendor", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickProduct(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_product", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickType(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_type", I32, CDECL, "I32", handle)
END FUNCTION
' The device GUID as 32 hexadecimal characters.
FUNCTION JoystickGuid(handle AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_guid", STRPTR, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickPlayerIndex(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_player_index", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickSetPlayerIndex(handle AS I32, index AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_set_player_index", I32, CDECL, "I32,I32", handle, index)
END FUNCTION
FUNCTION JoystickRumble(handle AS I32, low AS I32, high AS I32, ms AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_rumble", I32, CDECL, "I32,I32,I32,I32", handle, low, high, ms)
END FUNCTION
FUNCTION JoystickNumBalls(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_num_balls", I32, CDECL, "I32", handle)
END FUNCTION
' Relative motion of a trackball since the last read. which: 0 dx, 1 dy
FUNCTION JoystickBall(handle AS I32, ballIndex AS I32, which AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_ball", I32, CDECL, "I32,I32,I32", handle, ballIndex, which)
END FUNCTION
' Battery: state (see POWER_* in uxsdl3.bas) and percent (-1 unknown).
FUNCTION JoystickPowerState(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_power_state", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION JoystickPowerPercent(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_joystick_power_percent", I32, CDECL, "I32", handle)
END FUNCTION
' 0 unknown, 1 standard, 2 Xbox 360, 3 Xbox One, 4 PS3, 5 PS4, 6 PS5, 7 Switch Pro, ... (SDL_GamepadType)
FUNCTION GamepadType(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_type", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadTypeName(kind AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_type_name", STRPTR, CDECL, "I32", kind)
END FUNCTION
FUNCTION GamepadPlayerIndex(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_player_index", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadSetPlayerIndex(handle AS I32, index AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_set_player_index", I32, CDECL, "I32,I32", handle, index)
END FUNCTION
FUNCTION GamepadSetLED(handle AS I32, r AS I32, g AS I32, b AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_set_led", I32, CDECL, "I32,I32,I32,I32", handle, r, g, b)
END FUNCTION
FUNCTION GamepadPowerState(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_power_state", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadPowerPercent(handle AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_power_percent", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION GamepadRumbleTriggers(handle AS I32, left AS I32, right AS I32, ms AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_rumble_triggers", I32, CDECL, "I32,I32,I32,I32", handle, left, right, ms)
END FUNCTION
' Motion sensors: type 1 accelerometer (m/s^2), 2 gyroscope (rad/s).
FUNCTION GamepadHasSensor(handle AS I32, kind AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_has_sensor", I32, CDECL, "I32,I32", handle, kind)
END FUNCTION
FUNCTION GamepadSetSensorEnabled(handle AS I32, kind AS I32, enabled AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_set_sensor_enabled", I32, CDECL, "I32,I32,I32", handle, kind, enabled)
END FUNCTION
FUNCTION GamepadSensorEnabled(handle AS I32, kind AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_sensor_enabled", I32, CDECL, "I32,I32", handle, kind)
END FUNCTION
' Axis of the last sensor reading. index: 0 x, 1 y, 2 z
FUNCTION GamepadSensor(handle AS I32, kind AS I32, index AS I32) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_sensor", F64, CDECL, "I32,I32,I32", handle, kind, index)
END FUNCTION
FUNCTION GamepadMapping(handle AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_mapping", STRPTR, CDECL, "I32", handle)
END FUNCTION
' Adds or updates a mapping line (SDL_GameControllerDB format): 1 added, 0 updated, -1 invalid.
FUNCTION AddGamepadMapping(mapping AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_add_gamepad_mapping", I32, CDECL, "STRPTR", mapping)
END FUNCTION
FUNCTION GamepadButtonName(button AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_button_name", STRPTR, CDECL, "I32", button)
END FUNCTION
FUNCTION GamepadAxisName(axis AS I32) AS STRING
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_axis_name", STRPTR, CDECL, "I32", axis)
END FUNCTION
' -1 when the name is unknown
FUNCTION GamepadButtonFromName(name AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_button_from_name", I32, CDECL, "STRPTR", name)
END FUNCTION
FUNCTION GamepadAxisFromName(name AS STRING) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_axis_from_name", I32, CDECL, "STRPTR", name)
END FUNCTION
' Face-button label of this pad (1 A, 2 B, 3 X, 4 Y, 5 Cross, 6 Circle, 7 Square, 8 Triangle; 0 unknown).
FUNCTION GamepadButtonLabel(handle AS I32, button AS I32) AS I32
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_button_label", I32, CDECL, "I32,I32", handle, button)
END FUNCTION
' Axis normalized to -1.0 .. 1.0 with a dead zone: |value| below the dead zone reads 0.0, the rest is rescaled
' so the output still reaches +-1.0. deadZone 0.0 .. 0.99 (typical 0.15 for sticks).
FUNCTION GamepadAxisDeadZone(handle AS I32, axis AS I32, deadZone AS F64) AS F64
    RETURN CALL(DLL, "uxsdl3.dll", "uxsdl3_gamepad_axis_dead_zone", F64, CDECL, "I32,I32,F64", handle, axis, deadZone)
END FUNCTION

' ---- Conveniences built on the wrappers above ----
' Packs r,g,b,a (0..255) into one color value (r | g<<8 | b<<16 | a<<24), the layout of RenderReadPixel,
' TextureFill and TextureSetPixel (and of uxraylib colors).
FUNCTION PackRGBA(r AS I32, g AS I32, b AS I32, a AS I32) AS U32
    DIM packed AS I64
    packed = r
    packed = packed + g * 256
    packed = packed + b * 65536
    packed = packed + a * 16777216
    RETURN U32(packed)
END FUNCTION
FUNCTION UnpackR(rgba AS U32) AS I32
    DIM v AS I64
    v = rgba
    RETURN I32(v MOD 256)
END FUNCTION
FUNCTION UnpackG(rgba AS U32) AS I32
    DIM v AS I64
    v = rgba
    RETURN I32((v \ 256) MOD 256)
END FUNCTION
FUNCTION UnpackB(rgba AS U32) AS I32
    DIM v AS I64
    v = rgba
    RETURN I32((v \ 65536) MOD 256)
END FUNCTION
FUNCTION UnpackA(rgba AS U32) AS I32
    DIM v AS I64
    v = rgba
    RETURN I32((v \ 16777216) MOD 256)
END FUNCTION
' 1 when the window currently has the given WINDOW_* flag (e.g. HasWindowFlag(win, WINDOW_MAXIMIZED)).
FUNCTION HasWindowFlag(winHandle AS I64, flag AS I64) AS I32
    IF (GetWindowFlags(winHandle) AND flag) <> 0 THEN RETURN 1
    RETURN 0
END FUNCTION
FUNCTION GetDisplayWidth(displayId AS I32) AS I32
    RETURN DisplayBounds(displayId, 2)
END FUNCTION
FUNCTION GetDisplayHeight(displayId AS I32) AS I32
    RETURN DisplayBounds(displayId, 3)
END FUNCTION
FUNCTION GetWindowX(winHandle AS I64) AS I32
    RETURN GetWindowPosition(winHandle, 0)
END FUNCTION
FUNCTION GetWindowY(winHandle AS I64) AS I32
    RETURN GetWindowPosition(winHandle, 1)
END FUNCTION
FUNCTION GetWindowPixelWidth(winHandle AS I64) AS I32
    RETURN GetWindowPixelSize(winHandle, 0)
END FUNCTION
FUNCTION GetWindowPixelHeight(winHandle AS I64) AS I32
    RETURN GetWindowPixelSize(winHandle, 1)
END FUNCTION
FUNCTION RenderOutputWidth(rendererHandle AS I64) AS I32
    RETURN RenderOutputSize(rendererHandle, 0)
END FUNCTION
FUNCTION RenderOutputHeight(rendererHandle AS I64) AS I32
    RETURN RenderOutputSize(rendererHandle, 1)
END FUNCTION
' Sets the draw color from packed RGBA (see PackRGBA).
FUNCTION SetRenderDrawColorRGBA(rendererHandle AS I64, rgba AS U32) AS I32
    RETURN SetRenderDrawColor(rendererHandle, UnpackR(rgba), UnpackG(rgba), UnpackB(rgba), UnpackA(rgba))
END FUNCTION
END NAMESPACE

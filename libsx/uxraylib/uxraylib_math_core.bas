' uxraylib raymath core (S-052, raylib Models/3D dilimi 1). CPU only: no window or GL context is needed.
'
' Vector2/3/4 and Quaternion RESULTS are read from result registers: ResX/ResY/ResZ/ResW read register 0 (every plain
' result); functions with several results also fill registers 1 and 2 (read with ResGet(register, component 0..3)).
' A Matrix is a HANDLE (I32; 0 = invalid). Every function that produces a matrix returns a NEW handle: release it with
' MatrixRelease (MatrixLiveCount shows how many are still open). An invalid handle behaves as the identity matrix and
' MathLastError() becomes 1 (2 = handle pool full, 3 = bad vector slot); MathClearError() resets it.
' Matrix element index 0..15 follows raylib's field order (m0 m4 m8 m12 / m1 m5 m9 m13 / ...): the element in row r,
' column c has index c * 4 + r.
NAMESPACE uxraylib

FUNCTION ResGet(reg AS I32, component AS I32) AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_res_get", F64, CDECL, "I32,I32", reg, component)
END FUNCTION
FUNCTION ResX() AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_res_x", F64, CDECL)
END FUNCTION
FUNCTION ResY() AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_res_y", F64, CDECL)
END FUNCTION
FUNCTION ResZ() AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_res_z", F64, CDECL)
END FUNCTION
FUNCTION ResW() AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_res_w", F64, CDECL)
END FUNCTION

' Vector slots (0..7) feed the functions whose arguments would exceed the 10-value CALL(DLL) limit.
SUB VectorSlotSet(slotIndex AS I32, x AS F64, y AS F64, z AS F64, w AS F64)
    CALL(DLL, "uxraylib.dll", "uxraylib_vector_slot_set", VOID, CDECL, "I32,F64,F64,F64,F64", slotIndex, x, y, z, w)
END SUB

FUNCTION MathLastError() AS I32
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_math_last_error", I32, CDECL)
END FUNCTION
SUB MathClearError()
    CALL(DLL, "uxraylib.dll", "uxraylib_math_clear_error", VOID, CDECL)
END SUB

SUB MatrixRelease(handle AS I32)
    CALL(DLL, "uxraylib.dll", "uxraylib_matrix_release", VOID, CDECL, "I32", handle)
END SUB
FUNCTION MatrixLiveCount() AS I32
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_matrix_live_count", I32, CDECL)
END FUNCTION
FUNCTION MatrixCopy(handle AS I32) AS I32
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_matrix_copy", I32, CDECL, "I32", handle)
END FUNCTION
FUNCTION MatrixElement(handle AS I32, index AS I32) AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_matrix_element", F64, CDECL, "I32,I32", handle, index)
END FUNCTION
FUNCTION MatrixSetElement(handle AS I32, index AS I32, value AS F64) AS I32
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_matrix_set_element", I32, CDECL, "I32,I32,F64", handle, index, value)
END FUNCTION
' The element in ROW row, COLUMN col (both 0..3).
FUNCTION MatrixAt(handle AS I32, row AS I32, col AS I32) AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_matrix_element", F64, CDECL, "I32,I32", handle, col * 4 + row)
END FUNCTION

' Vector3OrthoNormalize: registers 0 and 1 receive the two orthonormalized vectors.
SUB Vector3OrthoNormalize(v1x AS F64, v1y AS F64, v1z AS F64, v2x AS F64, v2y AS F64, v2z AS F64)
    CALL(DLL, "uxraylib.dll", "uxraylib_vector3_ortho_normalize", VOID, CDECL, "F64,F64,F64,F64,F64,F64", v1x, v1y, v1z, v2x, v2y, v2z)
END SUB
' QuaternionToAxisAngle: returns the angle in radians; the axis is in register 0.
FUNCTION QuaternionToAxisAngle(qx AS F64, qy AS F64, qz AS F64, qw AS F64) AS F64
    RETURN CALL(DLL, "uxraylib.dll", "uxraylib_quaternion_to_axis_angle", F64, CDECL, "F64,F64,F64,F64", qx, qy, qz, qw)
END FUNCTION
' MatrixDecompose: register 0 = translation, 1 = rotation quaternion, 2 = scale.
SUB MatrixDecompose(handle AS I32)
    CALL(DLL, "uxraylib.dll", "uxraylib_matrix_decompose", VOID, CDECL, "I32", handle)
END SUB

' Slot variants (VectorSlotSet first): Vector3CubicHermite, Vector3Barycenter, QuaternionCubicHermiteSpline.
SUB Vector3CubicHermiteSlots(v1Slot AS I32, tangent1Slot AS I32, v2Slot AS I32, tangent2Slot AS I32, amount AS F64)
    CALL(DLL, "uxraylib.dll", "uxraylib_vector3_cubic_hermite_slots", VOID, CDECL, "I32,I32,I32,I32,F64", v1Slot, tangent1Slot, v2Slot, tangent2Slot, amount)
END SUB
SUB Vector3BarycenterSlots(pSlot AS I32, aSlot AS I32, bSlot AS I32, cSlot AS I32)
    CALL(DLL, "uxraylib.dll", "uxraylib_vector3_barycenter_slots", VOID, CDECL, "I32,I32,I32,I32", pSlot, aSlot, bSlot, cSlot)
END SUB
SUB QuaternionCubicHermiteSplineSlots(q1Slot AS I32, outTangent1Slot AS I32, q2Slot AS I32, inTangent2Slot AS I32, t AS F64)
    CALL(DLL, "uxraylib.dll", "uxraylib_quaternion_cubic_hermite_spline_slots", VOID, CDECL, "I32,I32,I32,I32,F64", q1Slot, outTangent1Slot, q2Slot, inTangent2Slot, t)
END SUB

END NAMESPACE

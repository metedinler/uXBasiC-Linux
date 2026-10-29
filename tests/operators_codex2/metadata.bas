#include once "../../src/parser/parser/parser_adim08_operator_contract.fbs"
If ParserOpPrecedence("^") <= ParserOpPrecedence("AND") Then End 1
If ParserOpPrecedence("XOR") >= ParserOpPrecedence("AND") Then End 2
If ParserOpPrecedence("XOR") <= ParserOpPrecedence("OR") Then End 3
If ParserOpPrecedence("-U") <= ParserOpPrecedence("**") Then End 4
If ParserOpPrecedence("=") <> 90 Then End 5
If ParserOpPrecedence("=", 1) <> 10 Then End 6
If ParserOpIsRightAssociative("=") <> 0 Then End 7
If ParserOpIsRightAssociative("=", 1) = 0 Then End 8
If ParserOpIsRightAssociative("**") = 0 Then End 9
Print "OPERATOR_METADATA_PASS"

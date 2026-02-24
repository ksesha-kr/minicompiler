from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_BOOL = auto()
    KW_RETURN = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_VOID = auto()
    KW_STRUCT = auto()
    KW_FN = auto()

    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_MOD = auto()
    OP_ASSIGN = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_LT = auto()
    OP_LE = auto()
    OP_GT = auto()
    OP_GE = auto()
    OP_AND = auto()
    OP_OR = auto()
    OP_NOT = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()

    END_OF_FILE = auto()
    ERROR = auto()


class Token:
    def __init__(self, token_type: TokenType, lexeme: str, line: int, column: int, literal: Any = None):
        self.type = token_type
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.literal = literal

    def __str__(self):
        result = f"{self.line}:{self.column} {self.type.name} \"{self.lexeme}\""
        if self.literal is not None:
            result += f" {self.literal}"
        return result
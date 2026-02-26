from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

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

    ERROR = auto()
    END_OF_FILE = auto()


class Token:
    def __init__(self, token_type: TokenType, lexeme: str, line: int, column: int, value: Any = None):
        self.token_type = token_type
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.value = value

    def __str__(self) -> str:
        if self.token_type == TokenType.END_OF_FILE:
            return f"{self.line}:{self.column} END_OF_FILE \"\""

        if self.token_type == TokenType.ERROR:
            return f"{self.line}:{self.column} ERROR \"{self.lexeme}\" {self.value}"

        if self.token_type in (TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
            return f"{self.line}:{self.column} {self.token_type.name} \"{self.lexeme}\" {self.value}"

        if self.token_type == TokenType.STRING_LITERAL:
            return f"{self.line}:{self.column} {self.token_type.name} \"{self.lexeme}\" \"{self.value}\""

        if self.token_type == TokenType.IDENTIFIER and self.value is not None:
            return f"{self.line}:{self.column} {self.token_type.name} \"{self.lexeme}\" {self.value}"

        if self.lexeme:
            return f"{self.line}:{self.column} {self.token_type.name} \"{self.lexeme}\""
        return f"{self.line}:{self.column} {self.token_type.name}"

    def __repr__(self) -> str:
        return self.__str__()

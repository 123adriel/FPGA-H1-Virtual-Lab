"""
Token Definitions - FPGA-H1 Compiler
Defines all lexical token types and Token data structure.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Keywords
    DEVICE = auto()
    MODULE = auto()
    END = auto()
    INPUT = auto()
    OUTPUT = auto()
    INOUT = auto()
    WIRE = auto()
    CLOCK = auto()
    RESET = auto()
    REGISTER = auto()
    ASSIGN = auto()
    LUT = auto()
    INSTANCE = auto()
    OF = auto()
    CONNECT = auto()
    TO = auto()
    ENABLE = auto()

    # Identifiers and Literals
    IDENT = auto()
    INT_LIT = auto()
    HEX_LIT = auto()
    BIN_LIT = auto()

    # Operators
    ASSIGN_OP = auto()      # =
    LE_OP = auto()          # <=
    EQ_OP = auto()          # ==
    NE_OP = auto()          # !=
    LT_OP = auto()          # <
    LEQ_OP = auto()         # <=
    GT_OP = auto()          # >
    GEQ_OP = auto()         # >=
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    AMP = auto()            # &
    PIPE = auto()           # |
    CARET = auto()          # ^
    TILDE = auto()          # ~
    BANG = auto()           # !
    QUESTION = auto()       # ?
    COLON = auto()          # :
    ARROW = auto()          # =>

    # Delimiters
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    COMMA = auto()          # ,
    DOT = auto()            # .
    SEMICOLON = auto()      # ;

    # Special
    EOF = auto()


KEYWORDS = {
    "DEVICE": TokenType.DEVICE,
    "MODULE": TokenType.MODULE,
    "END": TokenType.END,
    "INPUT": TokenType.INPUT,
    "OUTPUT": TokenType.OUTPUT,
    "INOUT": TokenType.INOUT,
    "WIRE": TokenType.WIRE,
    "CLOCK": TokenType.CLOCK,
    "RESET": TokenType.RESET,
    "REGISTER": TokenType.REGISTER,
    "ASSIGN": TokenType.ASSIGN,
    "LUT": TokenType.LUT,
    "INSTANCE": TokenType.INSTANCE,
    "OF": TokenType.OF,
    "CONNECT": TokenType.CONNECT,
    "TO": TokenType.TO,
    "ENABLE": TokenType.ENABLE,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"

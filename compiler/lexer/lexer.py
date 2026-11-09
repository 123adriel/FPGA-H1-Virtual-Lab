"""
Lexer for H1L - FPGA-H1 Compiler
Scans H1L source code into a token stream with exact line and column tracking.
"""

from typing import List, Optional
from compiler.lexer.token import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"LexerError at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """Scans H1L source code into Token instances."""

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _skip_whitespace_and_comments(self) -> None:
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch in ' \t\r\n':
                self._advance()
            elif ch == '#' or (ch == '/' and self._peek(1) == '/'):
                # Single-line comment: skip until newline
                while self.pos < self.length and self.source[self.pos] != '\n':
                    self._advance()
            elif ch == '/' and self._peek(1) == '*':
                # Multi-line comment: skip until */
                self._advance()  # /
                self._advance()  # *
                while self.pos < self.length:
                    if self.source[self.pos] == '*' and self._peek(1) == '/':
                        self._advance()
                        self._advance()
                        break
                    self._advance()
            else:
                break

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            self._skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            start_line = self.line
            start_col = self.column
            ch = self.source[self.pos]

            # 1. Identifiers and Keywords
            if ch.isalpha() or ch == '_':
                ident = ""
                while self.pos < self.length and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
                    ident += self._advance()
                ttype = KEYWORDS.get(ident, TokenType.IDENT)
                tokens.append(Token(ttype, ident, start_line, start_col))

            # 2. Numbers and Literals (Hex, Bin, Dec)
            elif ch.isdigit():
                num_str = ""
                if ch == '0' and (self._peek(1) in ['x', 'X']):
                    self._advance()  # 0
                    self._advance()  # x
                    while self.pos < self.length and self.source[self.pos] in '0123456789abcdefABCDEF_':
                        c = self._advance()
                        if c != '_':
                            num_str += c
                    val = int(num_str, 16)
                    tokens.append(Token(TokenType.HEX_LIT, val, start_line, start_col))
                elif ch == '0' and (self._peek(1) in ['b', 'B']):
                    self._advance()  # 0
                    self._advance()  # b
                    while self.pos < self.length and self.source[self.pos] in '01_':
                        c = self._advance()
                        if c != '_':
                            num_str += c
                    val = int(num_str, 2)
                    tokens.append(Token(TokenType.BIN_LIT, val, start_line, start_col))
                else:
                    while self.pos < self.length and (self.source[self.pos].isdigit() or self.source[self.pos] == '_'):
                        c = self._advance()
                        if c != '_':
                            num_str += c
                    val = int(num_str, 10)
                    tokens.append(Token(TokenType.INT_LIT, val, start_line, start_col))

            # 3. Two-character and Single-character Operators
            elif ch == '=':
                self._advance()
                if self._peek() == '>':
                    self._advance()
                    tokens.append(Token(TokenType.ARROW, "=>", start_line, start_col))
                elif self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.EQ_OP, "==", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.ASSIGN_OP, "=", start_line, start_col))
            elif ch == '<':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.LE_OP, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LT_OP, "<", start_line, start_col))
            elif ch == '>':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.GEQ_OP, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GT_OP, ">", start_line, start_col))
            elif ch == '!':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.NE_OP, "!=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.BANG, "!", start_line, start_col))
            elif ch == '+':
                self._advance()
                tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
            elif ch == '-':
                self._advance()
                tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
            elif ch == '*':
                self._advance()
                tokens.append(Token(TokenType.STAR, "*", start_line, start_col))
            elif ch == '&':
                self._advance()
                tokens.append(Token(TokenType.AMP, "&", start_line, start_col))
            elif ch == '|':
                self._advance()
                tokens.append(Token(TokenType.PIPE, "|", start_line, start_col))
            elif ch == '^':
                self._advance()
                tokens.append(Token(TokenType.CARET, "^", start_line, start_col))
            elif ch == '~':
                self._advance()
                tokens.append(Token(TokenType.TILDE, "~", start_line, start_col))
            elif ch == '?':
                self._advance()
                tokens.append(Token(TokenType.QUESTION, "?", start_line, start_col))
            elif ch == ':':
                self._advance()
                tokens.append(Token(TokenType.COLON, ":", start_line, start_col))
            elif ch == ',':
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == '.':
                self._advance()
                tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
            elif ch == ';':
                self._advance()
                tokens.append(Token(TokenType.SEMICOLON, ";", start_line, start_col))
            elif ch == '(':
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ')':
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == '[':
                self._advance()
                tokens.append(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == ']':
                self._advance()
                tokens.append(Token(TokenType.RBRACKET, "]", start_line, start_col))
            elif ch == '{':
                self._advance()
                tokens.append(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == '}':
                self._advance()
                tokens.append(Token(TokenType.RBRACE, "}", start_line, start_col))
            else:
                raise LexerError(f"Unexpected character '{ch}'", start_line, start_col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

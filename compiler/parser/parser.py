"""
Parser for H1L - FPGA-H1 Compiler
Parses token stream into typed AST nodes with syntax error reporting.
"""

from typing import List, Optional, Dict, Any
from compiler.lexer.token import Token, TokenType
from compiler.ast.nodes import (
    ASTNode, DeviceNode, ModuleNode, SignalDeclNode, RegisterDeclNode,
    AssignNode, LutNode, InstanceNode, ConnectNode, ExpressionNode,
    SignalRefNode, NumberNode, UnaryOpNode, BinaryOpNode, TernaryNode, ConcatNode
)


class ParserError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        if token:
            super().__init__(f"ParserError at line {token.line}, column {token.column}: {message} (found {token.type.name} '{token.value}')")
            self.line = token.line
            self.column = token.column
        else:
            super().__init__(f"ParserError: {message}")
            self.line = 0
            self.column = 0


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _curr(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _match(self, *types: TokenType) -> bool:
        if self._curr().type in types:
            self.pos += 1
            return True
        return False

    def _expect(self, token_type: TokenType, err_msg: Optional[str] = None) -> Token:
        curr = self._curr()
        if curr.type != token_type:
            msg = err_msg or f"Expected {token_type.name}"
            raise ParserError(msg, curr)
        self.pos += 1
        return curr

    def parse(self) -> DeviceNode:
        """Parses a full H1L source file into a DeviceNode."""
        modules: Dict[str, ModuleNode] = {}
        device_node: Optional[DeviceNode] = None

        while not self._match(TokenType.EOF):
            # Optional semicolons
            if self._match(TokenType.SEMICOLON):
                continue

            if self._curr().type == TokenType.MODULE:
                mod = self._parse_module()
                modules[mod.name] = mod
            elif self._curr().type == TokenType.DEVICE:
                if device_node is not None:
                    raise ParserError("Multiple DEVICE blocks found; only one top-level DEVICE allowed", self._curr())
                device_node = self._parse_device()
            else:
                raise ParserError(f"Unexpected top-level statement '{self._curr().value}'", self._curr())

        if device_node is None:
            # If no DEVICE keyword was provided, wrap declarations into a default DEVICE
            raise ParserError("Missing required top-level 'DEVICE <name>' definition", self._curr())

        device_node.modules = modules
        return device_node

    def _parse_device(self) -> DeviceNode:
        tok_dev = self._expect(TokenType.DEVICE)
        tok_name = self._expect(TokenType.IDENT, "Expected device identifier")
        items = []

        while self._curr().type != TokenType.END and self._curr().type != TokenType.EOF:
            if self._match(TokenType.SEMICOLON):
                continue
            item = self._parse_declaration_or_statement()
            if item:
                items.append(item)

        self._expect(TokenType.END, "Expected 'END' to close DEVICE block")
        return DeviceNode(name=tok_name.value, items=items, line=tok_dev.line, column=tok_dev.column)

    def _parse_module(self) -> ModuleNode:
        tok_mod = self._expect(TokenType.MODULE)
        tok_name = self._expect(TokenType.IDENT, "Expected module identifier")
        items = []

        while self._curr().type != TokenType.END and self._curr().type != TokenType.EOF:
            if self._match(TokenType.SEMICOLON):
                continue
            item = self._parse_declaration_or_statement()
            if item:
                items.append(item)

        self._expect(TokenType.END, "Expected 'END' to close MODULE block")
        return ModuleNode(name=tok_name.value, items=items, line=tok_mod.line, column=tok_mod.column)

    def _parse_declaration_or_statement(self) -> Optional[ASTNode]:
        curr = self._curr()

        # 1. Ports and Wires
        if curr.type in [TokenType.INPUT, TokenType.OUTPUT, TokenType.INOUT, TokenType.WIRE, TokenType.CLOCK, TokenType.RESET]:
            return self._parse_signal_decl()

        # 2. Sequential Register
        elif curr.type == TokenType.REGISTER:
            return self._parse_register_decl()

        # 3. Combinational Assign
        elif curr.type == TokenType.ASSIGN:
            return self._parse_assign()

        # 4. Low-level LUT Primitive
        elif curr.type == TokenType.LUT:
            return self._parse_lut()

        # 5. Module Instance
        elif curr.type == TokenType.INSTANCE:
            return self._parse_instance()

        # 6. Direct Connect
        elif curr.type == TokenType.CONNECT:
            return self._parse_connect()

        else:
            raise ParserError(f"Unexpected token in block body: '{curr.value}'", curr)

    def _parse_signal_decl(self) -> ASTNode:
        dir_tok = self._curr()
        self.pos += 1
        direction = dir_tok.type.name

        decls = []
        while True:
            ident_tok = self._expect(TokenType.IDENT, "Expected signal identifier")
            width = 1
            if self._match(TokenType.LBRACKET):
                int_tok = self._expect(TokenType.INT_LIT, "Expected integer bus width or range")
                if self._match(TokenType.COLON):
                    # Range [high:low]
                    low_tok = self._expect(TokenType.INT_LIT)
                    width = abs(int_tok.value - low_tok.value) + 1
                else:
                    # Bus width [N]
                    width = int_tok.value
                self._expect(TokenType.RBRACKET)

            decls.append(SignalDeclNode(name=ident_tok.value, width=width, direction=direction, line=dir_tok.line, column=dir_tok.column))
            if not self._match(TokenType.COMMA):
                break

        # Return single node if 1 signal, or let caller handle list
        if len(decls) == 1:
            return decls[0]
        # Return composite or chain
        class MultiSignalDecl(ASTNode):
            def __init__(self, signals):
                super().__init__(line=dir_tok.line, column=dir_tok.column)
                self.signals = signals
        return MultiSignalDecl(decls)

    def _parse_register_decl(self) -> RegisterDeclNode:
        tok_reg = self._expect(TokenType.REGISTER)
        tok_name = self._expect(TokenType.IDENT, "Expected register name")
        width = 1
        if self._match(TokenType.LBRACKET):
            tok_w = self._expect(TokenType.INT_LIT)
            width = tok_w.value
            self._expect(TokenType.RBRACKET)

        # Assignment operator <=
        if not (self._match(TokenType.LE_OP) or self._match(TokenType.ASSIGN_OP)):
            raise ParserError("Expected '<=' in REGISTER declaration", self._curr())

        expr = self._parse_expression()

        # Optional CLOCK, ENABLE, RESET clauses
        clk_name = "CLK"
        enable_expr = None
        rst_name = None

        while self._curr().type in [TokenType.CLOCK, TokenType.ENABLE, TokenType.RESET]:
            if self._match(TokenType.CLOCK):
                clk_name = self._expect(TokenType.IDENT, "Expected clock identifier").value
            elif self._match(TokenType.ENABLE):
                enable_expr = self._parse_expression()
            elif self._match(TokenType.RESET):
                rst_name = self._expect(TokenType.IDENT, "Expected reset identifier").value

        return RegisterDeclNode(
            name=tok_name.value,
            width=width,
            expr=expr,
            clock_name=clk_name,
            enable_expr=enable_expr,
            reset_name=rst_name,
            line=tok_reg.line,
            column=tok_reg.column
        )

    def _parse_assign(self) -> AssignNode:
        tok_assign = self._expect(TokenType.ASSIGN)
        target = self._parse_signal_ref()
        self._expect(TokenType.ASSIGN_OP, "Expected '=' in ASSIGN statement")
        expr = self._parse_expression()
        return AssignNode(target=target, expr=expr, line=tok_assign.line, column=tok_assign.column)

    def _parse_lut(self) -> LutNode:
        tok_lut = self._expect(TokenType.LUT)
        tok_name = self._expect(TokenType.IDENT, "Expected LUT name")
        self._expect(TokenType.LPAREN)
        inputs = []
        for i in range(4):
            if self._curr().type in [TokenType.INT_LIT, TokenType.HEX_LIT, TokenType.BIN_LIT]:
                tok_lit = self._curr()
                self.pos += 1
                inputs.append(NumberNode(value=tok_lit.value, line=tok_lit.line, column=tok_lit.column))
            else:
                inputs.append(self._parse_signal_ref())
            if i < 3:
                self._expect(TokenType.COMMA)
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.ASSIGN_OP)
        tok_mask = self._curr()
        if tok_mask.type in [TokenType.HEX_LIT, TokenType.INT_LIT]:
            mask_val = tok_mask.value
            self.pos += 1
        else:
            raise ParserError("Expected hexadecimal 16-bit mask for LUT", tok_mask)

        return LutNode(name=tok_name.value, inputs=inputs, mask=mask_val, line=tok_lut.line, column=tok_lut.column)

    def _parse_instance(self) -> InstanceNode:
        tok_inst = self._expect(TokenType.INSTANCE)
        tok_iname = self._expect(TokenType.IDENT, "Expected instance name")
        self._expect(TokenType.OF, "Expected 'OF' in INSTANCE declaration")
        tok_mname = self._expect(TokenType.IDENT, "Expected module name to instantiate")
        self._expect(TokenType.LPAREN)

        port_map = {}
        if self._curr().type != TokenType.RPAREN:
            while True:
                pname = self._expect(TokenType.IDENT, "Expected port name").value
                self._expect(TokenType.ARROW, "Expected '=>' in port mapping")
                expr = self._parse_expression()
                port_map[pname] = expr
                if not self._match(TokenType.COMMA):
                    break
        self._expect(TokenType.RPAREN)
        return InstanceNode(name=tok_iname.value, module_name=tok_mname.value, port_map=port_map, line=tok_inst.line, column=tok_inst.column)

    def _parse_connect(self) -> ConnectNode:
        tok_conn = self._expect(TokenType.CONNECT)
        src = self._parse_signal_ref()
        self._expect(TokenType.TO, "Expected 'TO' in CONNECT statement")
        dest = self._parse_signal_ref()
        return ConnectNode(src=src, dest=dest, line=tok_conn.line, column=tok_conn.column)

    # -------------------------------------------------------------------------
    # Expression Parsing (Precedence Climbing / Recursive Descent)
    # -------------------------------------------------------------------------
    def _parse_expression(self) -> ExpressionNode:
        return self._parse_ternary()

    def _parse_ternary(self) -> ExpressionNode:
        expr = self._parse_logical_or()
        if self._match(TokenType.QUESTION):
            true_expr = self._parse_expression()
            self._expect(TokenType.COLON, "Expected ':' in ternary operator")
            false_expr = self._parse_expression()
            return TernaryNode(cond=expr, true_expr=true_expr, false_expr=false_expr, line=expr.line, column=expr.column)
        return expr

    def _parse_logical_or(self) -> ExpressionNode:
        expr = self._parse_logical_xor()
        while self._match(TokenType.PIPE):
            right = self._parse_logical_xor()
            expr = BinaryOpNode(op="|", left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_logical_xor(self) -> ExpressionNode:
        expr = self._parse_logical_and()
        while self._match(TokenType.CARET):
            right = self._parse_logical_and()
            expr = BinaryOpNode(op="^", left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_logical_and(self) -> ExpressionNode:
        expr = self._parse_equality()
        while self._match(TokenType.AMP):
            right = self._parse_equality()
            expr = BinaryOpNode(op="&", left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_equality(self) -> ExpressionNode:
        expr = self._parse_relational()
        while self._curr().type in [TokenType.EQ_OP, TokenType.NE_OP]:
            op = "==" if self._match(TokenType.EQ_OP) else "!="
            right = self._parse_relational()
            expr = BinaryOpNode(op=op, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_relational(self) -> ExpressionNode:
        expr = self._parse_additive()
        while self._curr().type in [TokenType.LT_OP, TokenType.LEQ_OP, TokenType.GT_OP, TokenType.GEQ_OP]:
            op_tok = self._curr()
            self.pos += 1
            op_str = "<" if op_tok.type == TokenType.LT_OP else "<=" if op_tok.type == TokenType.LEQ_OP else ">" if op_tok.type == TokenType.GT_OP else ">="
            right = self._parse_additive()
            expr = BinaryOpNode(op=op_str, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_additive(self) -> ExpressionNode:
        expr = self._parse_multiplicative()
        while self._curr().type in [TokenType.PLUS, TokenType.MINUS]:
            op = "+" if self._match(TokenType.PLUS) else "-"
            right = self._parse_multiplicative()
            expr = BinaryOpNode(op=op, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_multiplicative(self) -> ExpressionNode:
        expr = self._parse_unary()
        while self._match(TokenType.STAR):
            right = self._parse_unary()
            expr = BinaryOpNode(op="*", left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_unary(self) -> ExpressionNode:
        curr = self._curr()
        if curr.type in [TokenType.TILDE, TokenType.BANG, TokenType.MINUS]:
            self.pos += 1
            op = "~" if curr.type == TokenType.TILDE else "!" if curr.type == TokenType.BANG else "-"
            operand = self._parse_unary()
            return UnaryOpNode(op=op, operand=operand, line=curr.line, column=curr.column)
        return self._parse_primary()

    def _parse_primary(self) -> ExpressionNode:
        curr = self._curr()

        # Parenthesized expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        # Concatenation { a, b, c }
        elif self._match(TokenType.LBRACE):
            parts = []
            while True:
                parts.append(self._parse_expression())
                if not self._match(TokenType.COMMA):
                    break
            self._expect(TokenType.RBRACE)
            return ConcatNode(parts=parts, line=curr.line, column=curr.column)

        # Number Literals
        elif curr.type in [TokenType.INT_LIT, TokenType.HEX_LIT, TokenType.BIN_LIT]:
            self.pos += 1
            return NumberNode(value=curr.value, line=curr.line, column=curr.column)

        # Signal Reference
        elif curr.type == TokenType.IDENT:
            return self._parse_signal_ref()

        else:
            raise ParserError(f"Unexpected token in expression: '{curr.value}'", curr)

    def _parse_signal_ref(self) -> SignalRefNode:
        tok_id = self._expect(TokenType.IDENT)
        name = tok_id.value
        subfield = None
        index = None
        range_high = None
        range_low = None

        if self._match(TokenType.DOT):
            subfield = self._expect(TokenType.IDENT, "Expected subfield identifier after '.'").value

        if self._match(TokenType.LBRACKET):
            tok_idx = self._expect(TokenType.INT_LIT, "Expected integer in bit select or slice")
            if self._match(TokenType.COLON):
                tok_low = self._expect(TokenType.INT_LIT, "Expected integer for lower range bound")
                range_high = tok_idx.value
                range_low = tok_low.value
            else:
                index = tok_idx.value
            self._expect(TokenType.RBRACKET)

        return SignalRefNode(
            name=name,
            subfield=subfield,
            index=index,
            range_high=range_high,
            range_low=range_low,
            line=tok_id.line,
            column=tok_id.column
        )

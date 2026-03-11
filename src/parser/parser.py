from typing import List, Optional, Any
from src.lexer.token import Token, TokenType
from src.parser.ast import *


class ParseError(Exception):

    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Ошибка парсинга [{line}:{column}]: {message}")


class Parser:

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParseError] = []

    def parse(self) -> ProgramNode:
        try:
            return self._parse_program()
        except ParseError as e:
            self.errors.append(e)
            return ProgramNode()

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _is_at_end(self) -> bool:
        return self._peek().token_type == TokenType.END_OF_FILE

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False

    def _check(self, type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().token_type == type

    def _consume(self, type: TokenType, message: str) -> Token:
        if self._check(type):
            return self._advance()
        raise ParseError(message, self._peek().line, self._peek().column)

    def _synchronize(self):
        self._advance()

        while not self._is_at_end():
            if self._previous().token_type == TokenType.SEMICOLON:
                return

            if self._peek().token_type in [
                TokenType.KW_FN, TokenType.KW_STRUCT, TokenType.KW_IF,
                TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN,
                TokenType.RBRACE
            ]:
                return

            self._advance()

    def _parse_program(self) -> ProgramNode:
        declarations = []

        while not self._is_at_end():
            try:
                decl = self._parse_declaration()
                if decl:
                    declarations.append(decl)
                else:
                    self._advance()
            except ParseError as e:
                self.errors.append(e)
                self._synchronize()

        return ProgramNode(declarations, self.tokens[0].line if self.tokens else 0, 1)

    def _parse_declaration(self) -> Optional[DeclarationNode]:
        if self._check(TokenType.KW_FN):
            return self._parse_function_decl()
        if self._check(TokenType.KW_STRUCT):
            return self._parse_struct_decl()
        if self._check(TokenType.KW_INT) or self._check(TokenType.KW_FLOAT) or \
                self._check(TokenType.KW_BOOL):
            return self._parse_var_decl()

        return None

    def _parse_function_decl(self) -> FunctionDeclNode:
        self._advance()
        name_token = self._consume(TokenType.IDENTIFIER, "Ожидается имя функции после 'fn'")

        self._consume(TokenType.LPAREN, "Ожидается '(' после имени функции")

        parameters = []
        if not self._check(TokenType.RPAREN):
            parameters = self._parse_parameters()

        self._consume(TokenType.RPAREN, "Ожидается ')' после параметров")

        return_type = "void"
        if self._match(TokenType.OP_ARROW):
            return_type = self._parse_type()

        self._consume(TokenType.LBRACE, "Ожидается '{' после заголовка функции")
        body = self._parse_block()

        return FunctionDeclNode(return_type, name_token.lexeme, parameters, body,
                                name_token.line, name_token.column)

    def _parse_struct_decl(self) -> StructDeclNode:
        self._advance()
        name_token = self._consume(TokenType.IDENTIFIER, "Ожидается имя структуры после 'struct'")

        self._consume(TokenType.LBRACE, "Ожидается '{' после имени структуры")

        fields = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            try:
                field = self._parse_var_decl()
                if field:
                    fields.append(field)
            except ParseError:
                self._synchronize()

        self._consume(TokenType.RBRACE, "Ожидается '}' в конце структуры")

        return StructDeclNode(name_token.lexeme, fields, name_token.line, name_token.column)

    def _parse_parameters(self) -> List[ParamNode]:
        parameters = []

        parameters.append(self._parse_parameter())

        while self._match(TokenType.COMMA):
            parameters.append(self._parse_parameter())

        return parameters

    def _parse_parameter(self) -> ParamNode:
        param_type = self._parse_type()
        name_token = self._consume(TokenType.IDENTIFIER, "Ожидается имя параметра")

        return ParamNode(param_type, name_token.lexeme, name_token.line, name_token.column)

    def _parse_type(self) -> str:
        if self._match(TokenType.KW_INT):
            return "int"
        if self._match(TokenType.KW_FLOAT):
            return "float"
        if self._match(TokenType.KW_BOOL):
            return "bool"
        if self._match(TokenType.KW_VOID):
            return "void"

        token = self._consume(TokenType.IDENTIFIER, "Ожидается тип")
        return token.lexeme

    def _parse_var_decl(self) -> VarDeclStmtNode:
        var_type = self._parse_type()
        name_token = self._consume(TokenType.IDENTIFIER, "Ожидается имя переменной")

        initializer = None
        if self._match(TokenType.OP_ASSIGN):
            initializer = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Ожидается ';' после объявления переменной")

        return VarDeclStmtNode(var_type, name_token.lexeme, initializer,
                               name_token.line, name_token.column)

    def _parse_statement(self) -> StatementNode:
        if self._match(TokenType.LBRACE):
            return self._parse_block()
        if self._check(TokenType.KW_IF):
            return self._parse_if_stmt()
        if self._check(TokenType.KW_WHILE):
            return self._parse_while_stmt()
        if self._check(TokenType.KW_FOR):
            return self._parse_for_stmt()
        if self._check(TokenType.KW_RETURN):
            return self._parse_return_stmt()
        if self._check(TokenType.KW_INT) or self._check(TokenType.KW_FLOAT) or \
                self._check(TokenType.KW_BOOL):
            return self._parse_var_decl()

        return self._parse_expr_stmt()

    def _parse_block(self) -> BlockStmtNode:
        statements = []

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            statements.append(self._parse_statement())

        self._consume(TokenType.RBRACE, "Ожидается '}' после блока")

        return BlockStmtNode(statements, self._previous().line, self._previous().column)

    def _parse_if_stmt(self) -> IfStmtNode:
        if_token = self._peek()
        self._advance()
        self._consume(TokenType.LPAREN, "Ожидается '(' после 'if'")
        condition = self._parse_expression()
        self._consume(TokenType.RPAREN, "Ожидается ')' после условия if")

        then_branch = self._parse_statement()
        else_branch = None

        if self._match(TokenType.KW_ELSE):
            else_branch = self._parse_statement()

        return IfStmtNode(condition, then_branch, else_branch,
                          if_token.line, if_token.column)

    def _parse_while_stmt(self) -> WhileStmtNode:
        self._advance()
        self._consume(TokenType.LPAREN, "Ожидается '(' после 'while'")
        condition = self._parse_expression()
        self._consume(TokenType.RPAREN, "Ожидается ')' после условия while")

        body = self._parse_statement()

        return WhileStmtNode(condition, body, self._previous().line, self._previous().column)

    def _parse_for_stmt(self) -> ForStmtNode:
        self._advance()
        self._consume(TokenType.LPAREN, "Ожидается '(' после 'for'")

        init = None
        if not self._check(TokenType.SEMICOLON):
            init = self._parse_expr_stmt()

        self._consume(TokenType.SEMICOLON, "Ожидается ';' после инициализации for")

        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Ожидается ';' после условия for")

        update = None
        if not self._check(TokenType.RPAREN):
            update = self._parse_expression()

        self._consume(TokenType.RPAREN, "Ожидается ')' после заголовка for")

        body = self._parse_statement()

        return ForStmtNode(init, condition, update, body,
                           self._previous().line, self._previous().column)

    def _parse_return_stmt(self) -> ReturnStmtNode:
        keyword = self._previous()
        self._advance()

        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Ожидается ';' после return")

        return ReturnStmtNode(value, keyword.line, keyword.column)

    def _parse_expr_stmt(self) -> ExprStmtNode:
        expr = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Ожидается ';' после выражения")

        return ExprStmtNode(expr, self._previous().line, self._previous().column)

    def _parse_expression(self) -> ExpressionNode:
        return self._parse_assignment()

    def _parse_assignment(self) -> ExpressionNode:
        expr = self._parse_logical_or()

        if self._match(TokenType.OP_ASSIGN):
            operator = "="
            value = self._parse_assignment()
            expr = AssignmentExprNode(expr, operator, value,
                                      self._previous().line, self._previous().column)

        return expr

    def _parse_logical_or(self) -> ExpressionNode:
        expr = self._parse_logical_and()

        while self._match(TokenType.OP_OR):
            operator = "||"
            right = self._parse_logical_and()
            expr = BinaryExprNode(expr, operator, right,
                                  self._previous().line, self._previous().column)

        return expr

    def _parse_logical_and(self) -> ExpressionNode:
        expr = self._parse_equality()

        while self._match(TokenType.OP_AND):
            operator = "&&"
            right = self._parse_equality()
            expr = BinaryExprNode(expr, operator, right,
                                  self._previous().line, self._previous().column)

        return expr

    def _parse_equality(self) -> ExpressionNode:
        expr = self._parse_relational()

        while self._match(TokenType.OP_EQ, TokenType.OP_NE):
            operator = "==" if self._previous().token_type == TokenType.OP_EQ else "!="
            right = self._parse_relational()
            expr = BinaryExprNode(expr, operator, right,
                                  self._previous().line, self._previous().column)

        return expr

    def _parse_relational(self) -> ExpressionNode:
        expr = self._parse_additive()

        while self._match(TokenType.OP_LT, TokenType.OP_LE,
                          TokenType.OP_GT, TokenType.OP_GE):
            token = self._previous()
            if token.token_type == TokenType.OP_LT:
                operator = "<"
            elif token.token_type == TokenType.OP_LE:
                operator = "<="
            elif token.token_type == TokenType.OP_GT:
                operator = ">"
            else:
                operator = ">="

            right = self._parse_additive()
            expr = BinaryExprNode(expr, operator, right,
                                  token.line, token.column)

        return expr

    def _parse_additive(self) -> ExpressionNode:
        expr = self._parse_multiplicative()

        while self._match(TokenType.OP_PLUS, TokenType.OP_MINUS):
            operator = "+" if self._previous().token_type == TokenType.OP_PLUS else "-"
            right = self._parse_multiplicative()
            expr = BinaryExprNode(expr, operator, right,
                                  self._previous().line, self._previous().column)

        return expr

    def _parse_multiplicative(self) -> ExpressionNode:
        expr = self._parse_unary()

        while self._match(TokenType.OP_MUL, TokenType.OP_DIV, TokenType.OP_MOD):
            token = self._previous()
            if token.token_type == TokenType.OP_MUL:
                operator = "*"
            elif token.token_type == TokenType.OP_DIV:
                operator = "/"
            else:
                operator = "%"

            right = self._parse_unary()
            expr = BinaryExprNode(expr, operator, right,
                                  token.line, token.column)

        return expr

    def _parse_unary(self) -> ExpressionNode:
        if self._match(TokenType.OP_MINUS, TokenType.OP_NOT):
            operator = "-" if self._previous().token_type == TokenType.OP_MINUS else "!"
            operand = self._parse_unary()
            return UnaryExprNode(operator, operand,
                                 self._previous().line, self._previous().column)

        return self._parse_primary()

    def _parse_primary(self) -> ExpressionNode:
        if self._match(TokenType.INT_LITERAL):
            return LiteralExprNode(self._previous().value, "int",
                                   self._previous().line, self._previous().column)

        if self._match(TokenType.FLOAT_LITERAL):
            return LiteralExprNode(self._previous().value, "float",
                                   self._previous().line, self._previous().column)

        if self._match(TokenType.STRING_LITERAL):
            return LiteralExprNode(self._previous().value, "string",
                                   self._previous().line, self._previous().column)

        if self._match(TokenType.KW_TRUE, TokenType.KW_FALSE):
            value = self._previous().token_type == TokenType.KW_TRUE
            return LiteralExprNode(value, "bool",
                                   self._previous().line, self._previous().column)

        if self._match(TokenType.IDENTIFIER):
            name = self._previous().lexeme
            if self._match(TokenType.LPAREN):
                arguments = self._parse_arguments()
                self._consume(TokenType.RPAREN, "Ожидается ')' после аргументов функции")
                return CallExprNode(name, arguments,
                                    self._previous().line, self._previous().column)

            return IdentifierExprNode(name, self._previous().line, self._previous().column)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            if not self._match(TokenType.RPAREN):
                raise ParseError("Ожидается ')' после выражения",
                                 self._peek().line, self._peek().column)
            return expr

        raise ParseError("Ожидается выражение", self._peek().line, self._peek().column)

    def _parse_arguments(self) -> List[ExpressionNode]:
        arguments = []

        if not self._check(TokenType.RPAREN):
            arguments.append(self._parse_expression())

            while self._match(TokenType.COMMA):
                arguments.append(self._parse_expression())

        return arguments
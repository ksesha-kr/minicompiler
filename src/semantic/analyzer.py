from typing import Any, Optional, Union
from src.parser.ast import (
    ASTNode, ProgramNode, ExpressionNode, StatementNode, DeclarationNode,
    LiteralExprNode, IdentifierExprNode, BinaryExprNode, UnaryExprNode,
    CallExprNode, AssignmentExprNode, BlockStmtNode, ExprStmtNode,
    IfStmtNode, WhileStmtNode, ForStmtNode, ReturnStmtNode, VarDeclStmtNode,
    ParamNode, FunctionDeclNode, StructDeclNode
)
from src.semantic.symbol_table import SymbolTable, SymbolInfo, SymbolKind, Scope
from src.semantic.types import (
    Type, BaseType, StructType, FunctionType,
    TYPE_INT, TYPE_FLOAT, TYPE_BOOL, TYPE_VOID, TYPE_STRING, parse_type
)
from src.semantic.errors import SemanticErrorCollector, SemanticErrorKind


class SemanticAnalyzer:

    def __init__(self, filename: str = "<input>"):
        self.filename = filename
        self.symbol_table = SymbolTable()
        self.errors = SemanticErrorCollector(filename)
        self._current_function_return_type: Optional[Type] = None

    def analyze(self, ast: ProgramNode) -> bool:
        self._process_declarations(ast)

        self._check_program(ast)

        return not self.errors.has_errors()

    def _process_declarations(self, node: ASTNode) -> None:
        if isinstance(node, ProgramNode):
            for decl in node.declarations:
                self._process_declarations(decl)

        elif isinstance(node, FunctionDeclNode):
            param_types = [parse_type(p.param_type) for p in node.parameters]
            return_type = parse_type(node.return_type)
            func_type = FunctionType(return_type, param_types)

            func_symbol = SymbolInfo(
                name=node.name,
                symbol_type=func_type,
                kind=SymbolKind.FUNCTION,
                line=node.line,
                column=node.column,
                return_type=return_type,
                parameters=[]
            )

            for param in node.parameters:
                param_symbol = SymbolInfo(
                    name=param.name,
                    symbol_type=parse_type(param.param_type),
                    kind=SymbolKind.PARAMETER,
                    line=param.line,
                    column=param.column,
                    is_initialized=True
                )
                func_symbol.parameters.append(param_symbol)

            if not self.symbol_table.insert(node.name, func_symbol):
                existing = self.symbol_table.lookup(node.name)
                self.errors.error(
                    SemanticErrorKind.DUPLICATE_DECLARATION,
                    f"Дублирующее объявление функции '{node.name}'",
                    node.line, node.column,
                    context=f"fn {node.name}(...)",
                    suggestion=f"Функция уже объявлена на строке {existing.line}"
                )

        elif isinstance(node, StructDeclNode):
            struct_type = StructType(node.name)
            fields = {}

            for field_decl in node.fields:
                field_type = parse_type(field_decl.var_type)
                fields[field_decl.name] = field_type

            struct_type.fields = fields

            struct_symbol = SymbolInfo(
                name=node.name,
                symbol_type=struct_type,
                kind=SymbolKind.STRUCT,
                line=node.line,
                column=node.column,
                fields={}
            )

            for field_decl in node.fields:
                field_symbol = SymbolInfo(
                    name=field_decl.name,
                    symbol_type=parse_type(field_decl.var_type),
                    kind=SymbolKind.VARIABLE,
                    line=field_decl.line,
                    column=field_decl.column
                )
                struct_symbol.fields[field_decl.name] = field_symbol

            if not self.symbol_table.insert(node.name, struct_symbol):
                existing = self.symbol_table.lookup(node.name)
                self.errors.error(
                    SemanticErrorKind.DUPLICATE_DECLARATION,
                    f"Дублирующее объявление структуры '{node.name}'",
                    node.line, node.column,
                    suggestion=f"Структура уже объявлена на строке {existing.line}"
                )

        elif isinstance(node, VarDeclStmtNode):
            var_type = parse_type(node.var_type)
            var_symbol = SymbolInfo(
                name=node.name,
                symbol_type=var_type,
                kind=SymbolKind.VARIABLE,
                line=node.line,
                column=node.column,
                is_initialized=(node.initializer is not None)
            )

            if not self.symbol_table.insert(node.name, var_symbol):
                existing = self.symbol_table.lookup(node.name)
                self.errors.error(
                    SemanticErrorKind.DUPLICATE_DECLARATION,
                    f"Дублирующее объявление переменной '{node.name}'",
                    node.line, node.column,
                    suggestion=f"Переменная уже объявлена на строке {existing.line}"
                )

    def _check_program(self, node: ProgramNode) -> None:
        for decl in node.declarations:
            self._check_declaration(decl)

    def _check_declaration(self, node: DeclarationNode) -> None:
        if isinstance(node, FunctionDeclNode):
            self._check_function_decl(node)
        elif isinstance(node, StructDeclNode):
            pass
        elif isinstance(node, VarDeclStmtNode):
            self._check_var_decl(node)

    def _check_function_decl(self, node: FunctionDeclNode) -> None:
        self.symbol_table.enter_scope(f"function:{node.name}")

        for param in node.parameters:
            param_symbol = SymbolInfo(
                name=param.name,
                symbol_type=parse_type(param.param_type),
                kind=SymbolKind.PARAMETER,
                line=param.line,
                column=param.column,
                is_initialized=True
            )
            self.symbol_table.insert(param.name, param_symbol)

        old_return_type = self._current_function_return_type
        self._current_function_return_type = parse_type(node.return_type)

        self._check_statement(node.body)

        if self._current_function_return_type != TYPE_VOID:
            pass

        self._current_function_return_type = old_return_type
        self.symbol_table.exit_scope()

    def _check_var_decl(self, node: VarDeclStmtNode) -> None:
        var_type = parse_type(node.var_type)

        if node.initializer:
            init_type = self._check_expression(node.initializer)

            if init_type and not init_type.is_compatible_with(var_type):
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    f"Несовместимый тип инициализатора",
                    node.initializer.line, node.initializer.column,
                    expected=str(var_type),
                    found=str(init_type)
                )

            self.symbol_table.mark_initialized(node.name)

    def _check_statement(self, node: StatementNode) -> Optional[Type]:

        if isinstance(node, BlockStmtNode):
            self.symbol_table.enter_scope("block")
            for stmt in node.statements:
                self._check_statement(stmt)
            self.symbol_table.exit_scope()
            return None

        elif isinstance(node, ExprStmtNode):
            return self._check_expression(node.expression)

        elif isinstance(node, IfStmtNode):
            cond_type = self._check_expression(node.condition)
            if cond_type != TYPE_BOOL:
                self.errors.error(
                    SemanticErrorKind.INVALID_CONDITION_TYPE,
                    "Условие должно быть булевым типом",
                    node.condition.line, node.condition.column,
                    expected="bool",
                    found=str(cond_type) if cond_type else "unknown"
                )
            self._check_statement(node.then_branch)
            if node.else_branch:
                self._check_statement(node.else_branch)
            return None

        elif isinstance(node, WhileStmtNode):
            cond_type = self._check_expression(node.condition)
            if cond_type != TYPE_BOOL:
                self.errors.error(
                    SemanticErrorKind.INVALID_CONDITION_TYPE,
                    "Условие цикла должно быть булевым типом",
                    node.condition.line, node.condition.column,
                    expected="bool",
                    found=str(cond_type) if cond_type else "unknown"
                )
            self._check_statement(node.body)
            return None

        elif isinstance(node, ForStmtNode):
            if node.init:
                self._check_statement(node.init)
            if node.condition:
                cond_type = self._check_expression(node.condition)
                if cond_type != TYPE_BOOL:
                    self.errors.error(
                        SemanticErrorKind.INVALID_CONDITION_TYPE,
                        "Условие цикла for должно быть булевым типом",
                        node.condition.line, node.condition.column,
                        expected="bool",
                        found=str(cond_type) if cond_type else "unknown"
                    )
            if node.update:
                self._check_expression(node.update)
            self._check_statement(node.body)
            return None

        elif isinstance(node, ReturnStmtNode):
            if node.value:
                return_type = self._check_expression(node.value)
                expected = self._current_function_return_type

                if expected and return_type and not return_type.is_compatible_with(expected):
                    self.errors.error(
                        SemanticErrorKind.INVALID_RETURN_TYPE,
                        "Несовместимый тип возвращаемого значения",
                        node.value.line, node.value.column,
                        expected=str(expected),
                        found=str(return_type)
                    )
            else:
                if self._current_function_return_type != TYPE_VOID:
                    self.errors.error(
                        SemanticErrorKind.INVALID_RETURN_TYPE,
                        f"Функция должна возвращать значение типа {self._current_function_return_type}",
                        node.line, node.column,
                        expected=str(self._current_function_return_type),
                        found="void"
                    )
            return None

        elif isinstance(node, VarDeclStmtNode):
            self._check_var_decl(node)
            return None

        return None

    def _check_expression(self, node: ExpressionNode) -> Optional[Type]:
        node.inferred_type = None

        if isinstance(node, LiteralExprNode):
            node.inferred_type = parse_type(node.literal_type)
            return node.inferred_type

        elif isinstance(node, IdentifierExprNode):
            symbol = self.symbol_table.lookup(node.name)

            if symbol is None:
                self.errors.error(
                    SemanticErrorKind.UNDECLARED_IDENTIFIER,
                    f"Необъявленный идентификатор '{node.name}'",
                    node.line, node.column,
                    suggestion="Проверьте имя переменной или добавьте объявление"
                )
                return None

            if symbol.kind == SymbolKind.VARIABLE and not symbol.is_initialized:
                self.errors.error(
                    SemanticErrorKind.UNINITIALIZED_USE,
                    f"Использование неинициализированной переменной '{node.name}'",
                    node.line, node.column
                )

            node.inferred_type = symbol.symbol_type
            node.resolved_symbol = symbol
            return symbol.symbol_type

        elif isinstance(node, BinaryExprNode):
            left_type = self._check_expression(node.left)
            right_type = self._check_expression(node.right)

            result_type = self._check_binary_operator(
                node.operator, left_type, right_type,
                node.line, node.column
            )

            node.inferred_type = result_type
            return result_type

        elif isinstance(node, UnaryExprNode):
            operand_type = self._check_expression(node.operand)

            result_type = self._check_unary_operator(
                node.operator, operand_type,
                node.line, node.column
            )

            node.inferred_type = result_type
            return result_type

        elif isinstance(node, CallExprNode):
            return self._check_function_call(node)

        elif isinstance(node, AssignmentExprNode):
            return self._check_assignment(node)

        return None

    def _check_binary_operator(self, op: str, left: Optional[Type],
                               right: Optional[Type], line: int, column: int) -> Optional[Type]:
        if left is None or right is None:
            return None

        if op in ('+', '-', '*', '/', '%'):
            if not isinstance(left, BaseType) or left.name not in ('int', 'float'):
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    f"Левый операнд должен быть числовым типом",
                    line, column,
                    expected="int or float",
                    found=str(left)
                )
                return None

            if not isinstance(right, BaseType) or right.name not in ('int', 'float'):
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    f"Правый операнд должен быть числовым типом",
                    line, column,
                    expected="int or float",
                    found=str(right)
                )
                return None

            if left.name == 'float' or right.name == 'float':
                return TYPE_FLOAT
            return TYPE_INT

        elif op in ('==', '!=', '<', '<=', '>', '>='):
            if not left.is_compatible_with(right) and not right.is_compatible_with(left):
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    f"Несовместимые типы в сравнении",
                    line, column,
                    expected=str(left),
                    found=str(right)
                )
                return None
            return TYPE_BOOL

        elif op in ('&&', '||'):
            if left != TYPE_BOOL:
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    "Левый операнд логического оператора должен быть bool",
                    line, column,
                    expected="bool",
                    found=str(left)
                )
            if right != TYPE_BOOL:
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    "Правый операнд логического оператора должен быть bool",
                    line, column,
                    expected="bool",
                    found=str(right)
                )
            return TYPE_BOOL

        return None

    def _check_unary_operator(self, op: str, operand: Optional[Type],
                              line: int, column: int) -> Optional[Type]:
        if operand is None:
            return None

        if op == '-':
            if not isinstance(operand, BaseType) or operand.name not in ('int', 'float'):
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    "Операнд унарного минуса должен быть числовым",
                    line, column,
                    expected="int or float",
                    found=str(operand)
                )
                return None
            return operand

        elif op == '!':
            if operand != TYPE_BOOL:
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    "Операнд логического НЕ должен быть bool",
                    line, column,
                    expected="bool",
                    found=str(operand)
                )
                return None
            return TYPE_BOOL

        return None

    def _check_function_call(self, node: CallExprNode) -> Optional[Type]:
        symbol = self.symbol_table.lookup(node.callee)

        if symbol is None:
            self.errors.error(
                SemanticErrorKind.UNDECLARED_IDENTIFIER,
                f"Необъявленная функция '{node.callee}'",
                node.line, node.column,
                suggestion="Проверьте имя функции или добавьте объявление"
            )
            return None

        if symbol.kind != SymbolKind.FUNCTION:
            self.errors.error(
                SemanticErrorKind.TYPE_MISMATCH,
                f"'{node.callee}' не является функцией",
                node.line, node.column,
                expected="function",
                found=str(symbol.kind.name.lower())
            )
            return None

        func_type = symbol.symbol_type
        if not isinstance(func_type, FunctionType):
            return None

        if len(node.arguments) != len(func_type.param_types):
            self.errors.error(
                SemanticErrorKind.ARGUMENT_COUNT_MISMATCH,
                f"Неверное количество аргументов",
                node.line, node.column,
                expected=f"{len(func_type.param_types)} arguments",
                found=f"{len(node.arguments)} arguments",
                suggestion=f"Сигнатура: {node.callee}({', '.join(str(t) for t in func_type.param_types)})"
            )
            return func_type.return_type

        for i, (arg, param_type) in enumerate(zip(node.arguments, func_type.param_types)):
            arg_type = self._check_expression(arg)
            if arg_type and not arg_type.is_compatible_with(param_type):
                self.errors.error(
                    SemanticErrorKind.ARGUMENT_TYPE_MISMATCH,
                    f"Несовместимый тип аргумента #{i + 1}",
                    arg.line, arg.column,
                    expected=str(param_type),
                    found=str(arg_type)
                )

        return func_type.return_type

    def _check_assignment(self, node: AssignmentExprNode) -> Optional[Type]:
        if isinstance(node.target, IdentifierExprNode):
            symbol = self.symbol_table.lookup(node.target.name)
            if symbol is None:
                self.errors.error(
                    SemanticErrorKind.UNDECLARED_IDENTIFIER,
                    f"Необъявленная переменная '{node.target.name}'",
                    node.target.line, node.target.column
                )
                return None

            target_type = symbol.symbol_type
            self.symbol_table.mark_initialized(node.target.name)

        elif isinstance(node.target, BinaryExprNode):
            target_type = self._check_expression(node.target)
        else:
            self.errors.error(
                SemanticErrorKind.INVALID_ASSIGNMENT_TARGET,
                "Левая часть присваивания должна быть переменной",
                node.target.line, node.target.column
            )
            return None

        value_type = self._check_expression(node.value)

        if target_type and value_type:
            if not value_type.is_compatible_with(target_type):
                self.errors.error(
                    SemanticErrorKind.TYPE_MISMATCH,
                    "Несовместимый тип в присваивании",
                    node.value.line, node.value.column,
                    expected=str(target_type),
                    found=str(value_type)
                )

        node.inferred_type = target_type
        return target_type

    def get_errors(self):
        return self.errors.get_errors()

    def get_symbol_table(self) -> SymbolTable:
        return self.symbol_table

    def get_decorated_ast(self, ast: ProgramNode) -> ProgramNode:
        return ast

    def dump_decorated_ast(self, node: ASTNode, indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent

        def type_annotation(node: ASTNode) -> str:
            t = getattr(node, 'inferred_type', None)
            return f" [type: {t}]" if t else ""

        def format_expr(expr) -> str:
            if expr is None:
                return "<none>"
            if isinstance(expr, LiteralExprNode):
                return f"Literal: {expr.value} ({expr.literal_type}){type_annotation(expr)}"
            elif isinstance(expr, IdentifierExprNode):
                symbol = getattr(expr, 'resolved_symbol', None)
                sym_info = f" -> {symbol.name}" if symbol else ""
                return f"Identifier: {expr.name}{sym_info}{type_annotation(expr)}"
            elif isinstance(expr, BinaryExprNode):
                return f"Binary({expr.operator}){type_annotation(expr)}"
            elif isinstance(expr, CallExprNode):
                return f"Call: {expr.callee}{type_annotation(expr)}"
            else:
                return f"<expr>{type_annotation(expr)}"

        if isinstance(node, ProgramNode):
            lines.append(f"{prefix}Program{type_annotation(node)}:")
            for decl in node.declarations:
                lines.append(self.dump_decorated_ast(decl, indent + 1))

        elif isinstance(node, FunctionDeclNode):
            params = ", ".join(f"{p.name}: {p.param_type}" for p in node.parameters)
            lines.append(f"{prefix}FunctionDecl: {node.name}({params}) -> {node.return_type}{type_annotation(node)}:")
            for param in node.parameters:
                lines.append(f"{prefix}  Param: {param.name}: {param.param_type}")
            lines.append(f"{prefix}  Body:")
            lines.append(self.dump_decorated_ast(node.body, indent + 2))

        elif isinstance(node, BlockStmtNode):
            lines.append(f"{prefix}Block{type_annotation(node)}:")
            for stmt in node.statements:
                lines.append(self.dump_decorated_ast(stmt, indent + 1))

        elif isinstance(node, VarDeclStmtNode):
            if node.initializer:
                init_str = self._format_expr(node.initializer)
                lines.append(f"{prefix}VarDecl: {node.var_type} {node.name} = {init_str}")
            else:
                lines.append(f"{prefix}VarDecl: {node.var_type} {node.name}")

        elif isinstance(node, ReturnStmtNode):
            if node.value:
                lines.append(f"{prefix}Return{type_annotation(node.value)}:")
                lines.append(self.dump_decorated_ast(node.value, indent + 1))
            else:
                lines.append(f"{prefix}Return: void")

        elif isinstance(node, IfStmtNode):
            lines.append(f"{prefix}If{type_annotation(node.condition)}:")
            lines.append(f"{prefix}  Condition:")
            lines.append(self.dump_decorated_ast(node.condition, indent + 2))
            lines.append(f"{prefix}  Then:")
            lines.append(self.dump_decorated_ast(node.then_branch, indent + 2))
            if node.else_branch:
                lines.append(f"{prefix}  Else:")
                lines.append(self.dump_decorated_ast(node.else_branch, indent + 2))

        elif isinstance(node, WhileStmtNode):
            lines.append(f"{prefix}While{type_annotation(node.condition)}:")
            lines.append(f"{prefix}  Condition:")
            lines.append(self.dump_decorated_ast(node.condition, indent + 2))
            lines.append(f"{prefix}  Body:")
            lines.append(self.dump_decorated_ast(node.body, indent + 2))

        elif isinstance(node, ExprStmtNode):
            lines.append(f"{prefix}ExprStmt{type_annotation(node.expression)}:")
            if node.expression:
                lines.append(self.dump_decorated_ast(node.expression, indent + 1))

        elif isinstance(node, AssignmentExprNode):
            lines.append(f"{prefix}Assignment: {node.operator}{type_annotation(node)}:")
            lines.append(f"{prefix}  Target:")
            lines.append(self.dump_decorated_ast(node.target, indent + 2))
            lines.append(f"{prefix}  Value:")
            lines.append(self.dump_decorated_ast(node.value, indent + 2))

        elif isinstance(node, BinaryExprNode):
            lines.append(f"{prefix}Binary({node.operator}){type_annotation(node)}:")
            lines.append(f"{prefix}  Left:")
            lines.append(self.dump_decorated_ast(node.left, indent + 2))
            lines.append(f"{prefix}  Right:")
            lines.append(self.dump_decorated_ast(node.right, indent + 2))

        elif isinstance(node, UnaryExprNode):
            lines.append(f"{prefix}Unary({node.operator}){type_annotation(node)}:")
            lines.append(f"{prefix}  Operand:")
            lines.append(self.dump_decorated_ast(node.operand, indent + 2))

        elif isinstance(node, LiteralExprNode):
            lines.append(f"{prefix}Literal: {node.value} ({node.literal_type}){type_annotation(node)}")

        elif isinstance(node, IdentifierExprNode):
            symbol = getattr(node, 'resolved_symbol', None)
            sym_info = f" -> {symbol.name}" if symbol else ""
            lines.append(f"{prefix}Identifier: {node.name}{sym_info}{type_annotation(node)}")

        elif isinstance(node, CallExprNode):
            lines.append(f"{prefix}Call: {node.callee}{type_annotation(node)}:")
            lines.append(f"{prefix}  Arguments:")
            for arg in node.arguments:
                lines.append(self.dump_decorated_ast(arg, indent + 2))

        else:
            node_type = type(node).__name__.replace('Node', '')
            lines.append(f"{prefix}{node_type}{type_annotation(node)}")

        return "\n".join(lines)

    def _format_expr(self, expr: ExpressionNode, indent: int = 0) -> str:
        prefix = "  " * indent

        if isinstance(expr, LiteralExprNode):
            return f"Literal: {expr.value} ({expr.literal_type}) [type: {getattr(expr, 'inferred_type', expr.literal_type)}]"
        elif isinstance(expr, IdentifierExprNode):
            symbol = getattr(expr, 'resolved_symbol', None)
            sym_info = f" -> {symbol.name}" if symbol else ""
            return f"Identifier: {expr.name}{sym_info} [type: {getattr(expr, 'inferred_type', 'unknown')}]"
        elif isinstance(expr, BinaryExprNode):
            return f"Binary({expr.operator}) [type: {getattr(expr, 'inferred_type', 'unknown')}]:"
        elif isinstance(expr, CallExprNode):
            return f"Call: {expr.callee} [type: {getattr(expr, 'inferred_type', 'unknown')}]:"
        else:
            return f"<expr> [type: {getattr(expr, 'inferred_type', 'unknown')}]"
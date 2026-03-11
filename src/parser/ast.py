from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass, field


class ASTNode(ABC):

    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column

    @abstractmethod
    def __str__(self, indent: int = 0) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class ProgramNode(ASTNode):

    def __init__(self, declarations: List[ASTNode] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.declarations = declarations or []

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Program [line {self.line}]:\n"
        for decl in self.declarations:
            result += decl.__str__(indent + 2)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "Program",
            "line": self.line,
            "column": self.column,
            "declarations": [d.to_dict() for d in self.declarations]
        }


class ExpressionNode(ASTNode):
    pass


class LiteralExprNode(ExpressionNode):

    def __init__(self, value: Any, literal_type: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value
        self.literal_type = literal_type

    def __str__(self, indent: int = 0) -> str:
        return " " * indent + f"Literal: {self.value} ({self.literal_type}) [line {self.line}]\n"

    def to_dict(self) -> dict:
        return {
            "type": "Literal",
            "line": self.line,
            "column": self.column,
            "value": self.value,
            "literal_type": self.literal_type
        }


class IdentifierExprNode(ExpressionNode):

    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name

    def __str__(self, indent: int = 0) -> str:
        return " " * indent + f"Identifier: {self.name} [line {self.line}]\n"

    def to_dict(self) -> dict:
        return {
            "type": "Identifier",
            "line": self.line,
            "column": self.column,
            "name": self.name
        }


class BinaryExprNode(ExpressionNode):

    def __init__(self, left: ExpressionNode, operator: str, right: ExpressionNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Binary: {self.operator} [line {self.line}]\n"
        result += " " * (indent + 2) + "Left:\n"
        result += self.left.__str__(indent + 4)
        result += " " * (indent + 2) + "Right:\n"
        result += self.right.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "Binary",
            "line": self.line,
            "column": self.column,
            "operator": self.operator,
            "left": self.left.to_dict(),
            "right": self.right.to_dict()
        }


class UnaryExprNode(ExpressionNode):

    def __init__(self, operator: str, operand: ExpressionNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Unary: {self.operator} [line {self.line}]\n"
        result += " " * (indent + 2) + "Operand:\n"
        result += self.operand.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "Unary",
            "line": self.line,
            "column": self.column,
            "operator": self.operator,
            "operand": self.operand.to_dict()
        }


class CallExprNode(ExpressionNode):

    def __init__(self, callee: str, arguments: List[ExpressionNode],
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.callee = callee
        self.arguments = arguments

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Call: {self.callee} [line {self.line}]\n"
        result += " " * (indent + 2) + "Arguments:\n"
        for arg in self.arguments:
            result += arg.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "Call",
            "line": self.line,
            "column": self.column,
            "callee": self.callee,
            "arguments": [a.to_dict() for a in self.arguments]
        }


class AssignmentExprNode(ExpressionNode):

    def __init__(self, target: ExpressionNode, operator: str, value: ExpressionNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.target = target
        self.operator = operator
        self.value = value

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Assignment: {self.operator} [line {self.line}]\n"
        result += " " * (indent + 2) + "Target:\n"
        result += self.target.__str__(indent + 4)
        result += " " * (indent + 2) + "Value:\n"
        result += self.value.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "Assignment",
            "line": self.line,
            "column": self.column,
            "operator": self.operator,
            "target": self.target.to_dict(),
            "value": self.value.to_dict()
        }


class StatementNode(ASTNode):
    pass


class BlockStmtNode(StatementNode):

    def __init__(self, statements: List[StatementNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.statements = statements

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Block [line {self.line}]:\n"
        for stmt in self.statements:
            result += stmt.__str__(indent + 2)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "Block",
            "line": self.line,
            "column": self.column,
            "statements": [s.to_dict() for s in self.statements]
        }


class ExprStmtNode(StatementNode):

    def __init__(self, expression: ExpressionNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.expression = expression

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"ExprStmt [line {self.line}]:\n"
        result += self.expression.__str__(indent + 2)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "ExprStmt",
            "line": self.line,
            "column": self.column,
            "expression": self.expression.to_dict()
        }


class IfStmtNode(StatementNode):

    def __init__(self, condition: ExpressionNode, then_branch: StatementNode,
                 else_branch: Optional[StatementNode] = None,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"IfStmt [line {self.line}]:\n"
        result += " " * (indent + 2) + "Condition:\n"
        result += self.condition.__str__(indent + 4)
        result += " " * (indent + 2) + "Then:\n"
        result += self.then_branch.__str__(indent + 4)
        if self.else_branch:
            result += " " * (indent + 2) + "Else:\n"
            result += self.else_branch.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        result = {
            "type": "If",
            "line": self.line,
            "column": self.column,
            "condition": self.condition.to_dict(),
            "then_branch": self.then_branch.to_dict()
        }
        if self.else_branch:
            result["else_branch"] = self.else_branch.to_dict()
        return result


class WhileStmtNode(StatementNode):

    def __init__(self, condition: ExpressionNode, body: StatementNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"WhileStmt [line {self.line}]:\n"
        result += " " * (indent + 2) + "Condition:\n"
        result += self.condition.__str__(indent + 4)
        result += " " * (indent + 2) + "Body:\n"
        result += self.body.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "While",
            "line": self.line,
            "column": self.column,
            "condition": self.condition.to_dict(),
            "body": self.body.to_dict()
        }


class ForStmtNode(StatementNode):

    def __init__(self, init: Optional[StatementNode], condition: Optional[ExpressionNode],
                 update: Optional[ExpressionNode], body: StatementNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"ForStmt [line {self.line}]:\n"
        if self.init:
            result += " " * (indent + 2) + "Init:\n"
            result += self.init.__str__(indent + 4)
        if self.condition:
            result += " " * (indent + 2) + "Condition:\n"
            result += self.condition.__str__(indent + 4)
        if self.update:
            result += " " * (indent + 2) + "Update:\n"
            result += self.update.__str__(indent + 4)
        result += " " * (indent + 2) + "Body:\n"
        result += self.body.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        result = {
            "type": "For",
            "line": self.line,
            "column": self.column,
            "body": self.body.to_dict()
        }
        if self.init:
            result["init"] = self.init.to_dict()
        if self.condition:
            result["condition"] = self.condition.to_dict()
        if self.update:
            result["update"] = self.update.to_dict()
        return result


class ReturnStmtNode(StatementNode):

    def __init__(self, value: Optional[ExpressionNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"Return [line {self.line}]:\n"
        if self.value:
            result += self.value.__str__(indent + 2)
        else:
            result += " " * (indent + 2) + "null\n"
        return result

    def to_dict(self) -> dict:
        result = {
            "type": "Return",
            "line": self.line,
            "column": self.column
        }
        if self.value:
            result["value"] = self.value.to_dict()
        return result


class VarDeclStmtNode(StatementNode):

    def __init__(self, var_type: str, name: str,
                 initializer: Optional[ExpressionNode] = None,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.var_type = var_type
        self.name = name
        self.initializer = initializer

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"VarDecl: {self.var_type} {self.name}"
        if self.initializer:
            result += " = "
            result += self.initializer.__str__(0).strip()
        result += f" [line {self.line}]\n"
        return result

    def to_dict(self) -> dict:
        result = {
            "type": "VarDecl",
            "line": self.line,
            "column": self.column,
            "var_type": self.var_type,
            "name": self.name
        }
        if self.initializer:
            result["initializer"] = self.initializer.to_dict()
        return result

class DeclarationNode(ASTNode):
    pass


class ParamNode(ASTNode):

    def __init__(self, param_type: str, name: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.param_type = param_type
        self.name = name

    def __str__(self, indent: int = 0) -> str:
        return " " * indent + f"Param: {self.param_type} {self.name} [line {self.line}]\n"

    def to_dict(self) -> dict:
        return {
            "type": "Param",
            "line": self.line,
            "column": self.column,
            "param_type": self.param_type,
            "name": self.name
        }


class FunctionDeclNode(DeclarationNode):

    def __init__(self, return_type: str, name: str, parameters: List[ParamNode],
                 body: BlockStmtNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.return_type = return_type
        self.name = name
        self.parameters = parameters
        self.body = body

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"FunctionDecl: {self.name} -> {self.return_type} [line {self.line}]:\n"
        result += " " * (indent + 2) + "Parameters:\n"
        for param in self.parameters:
            result += param.__str__(indent + 4)
        if not self.parameters:
            result += " " * (indent + 4) + "[]\n"
        result += " " * (indent + 2) + "Body:\n"
        result += self.body.__str__(indent + 4)
        return result

    def to_dict(self) -> dict:
        return {
            "type": "FunctionDecl",
            "line": self.line,
            "column": self.column,
            "return_type": self.return_type,
            "name": self.name,
            "parameters": [p.to_dict() for p in self.parameters],
            "body": self.body.to_dict()
        }


class StructDeclNode(DeclarationNode):

    def __init__(self, name: str, fields: List[VarDeclStmtNode],
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
        self.fields = fields

    def __str__(self, indent: int = 0) -> str:
        result = " " * indent + f"StructDecl: {self.name} [line {self.line}]:\n"
        result += " " * (indent + 2) + "Fields:\n"
        for field in self.fields:
            result += field.__str__(indent + 4)
        if not self.fields:
            result += " " * (indent + 4) + "[]\n"
        return result

    def to_dict(self) -> dict:
        return {
            "type": "StructDecl",
            "line": self.line,
            "column": self.column,
            "name": self.name,
            "fields": [f.to_dict() for f in self.fields]
        }
from typing import Optional, List, Union
from src.parser.ast import (
    ASTNode, ProgramNode, ExpressionNode, StatementNode, DeclarationNode,
    LiteralExprNode, IdentifierExprNode, BinaryExprNode, UnaryExprNode,
    CallExprNode, AssignmentExprNode, BlockStmtNode, ExprStmtNode,
    IfStmtNode, WhileStmtNode, ForStmtNode, ReturnStmtNode, VarDeclStmtNode,
    ParamNode, FunctionDeclNode, StructDeclNode
)
from src.ir.function import FunctionIR, ProgramIR
from src.ir.basic_block import BasicBlock, BlockType, ControlFlowGraph
from src.ir.operand import (
    Operand, TempOperand, VarOperand, LiteralOperand, LabelOperand, MemoryOperand,
    temp, var, literal, label, memory
)
from src.ir.instructions import (
    Instruction, BinaryArithInst, UnaryArithInst, BinaryLogicInst, UnaryLogicInst,
    CmpInst, LoadInst, StoreInst, AllocaInst, JumpInst, CondJumpInst, LabelInst,
    PhiInst, CallInst, ReturnInst, ParamInst,
    add, sub, mul, div, cmp_eq, cmp_lt, load, store, jump, jump_if, jump_if_not,
    label as make_label, call, ret,
    InstructionType
)
from src.semantic.symbol_table import SymbolTable, SymbolInfo, SymbolKind
from src.semantic.types import Type, BaseType, TYPE_INT, TYPE_FLOAT, TYPE_BOOL


class IRGenerator:

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.program_ir = ProgramIR()
        self.current_function: Optional[FunctionIR] = None
        self.current_block: Optional[BasicBlock] = None

    def generate(self, ast: ProgramNode) -> ProgramIR:
        for decl in ast.declarations:
            self._generate_declaration(decl)
        return self.program_ir

    def _generate_declaration(self, node: DeclarationNode) -> None:
        if isinstance(node, FunctionDeclNode):
            self._generate_function(node)
        elif isinstance(node, StructDeclNode):
            pass
        elif isinstance(node, VarDeclStmtNode):
            self._generate_global_var(node)

    def _generate_global_var(self, node: VarDeclStmtNode) -> None:
        self.program_ir.global_vars[node.name] = {
            "type": node.var_type,
            "initialized": node.initializer is not None
        }

    def _generate_function(self, node: FunctionDeclNode) -> None:
        func_ir = FunctionIR(
            name=node.name,
            return_type=node.return_type,
            parameters=[(p.name, p.param_type) for p in node.parameters]
        )

        for i, param in enumerate(node.parameters):
            func_ir.register_parameter(param.name, param.param_type, i)

        entry = func_ir.create_block("entry", BlockType.ENTRY)
        func_ir.cfg.entry_block = entry

        old_function = self.current_function
        old_block = self.current_block
        self.current_function = func_ir
        self.current_block = entry

        self._collect_locals(node.body)
        func_ir.generate_prologue(entry)

        self._generate_statement(node.body)

        if not entry.is_terminated() and node.return_type == "void":
            entry.add_instruction(ret())

        self.program_ir.add_function(func_ir)

        self.current_function = old_function
        self.current_block = old_block

    def _collect_locals(self, node: StatementNode) -> None:
        if isinstance(node, BlockStmtNode):
            for stmt in node.statements:
                self._collect_locals(stmt)
        elif isinstance(node, VarDeclStmtNode):
            if self.current_function:
                self.current_function.allocate_local(
                    node.name, node.var_type
                )
        elif isinstance(node, IfStmtNode):
            self._collect_locals(node.then_branch)
            if node.else_branch:
                self._collect_locals(node.else_branch)
        elif isinstance(node, WhileStmtNode):
            self._collect_locals(node.body)
        elif isinstance(node, ForStmtNode):
            if node.init:
                self._collect_locals(node.init)
            self._collect_locals(node.body)

    def _generate_statement(self, node: StatementNode) -> Optional[Operand]:
        if isinstance(node, BlockStmtNode):
            for stmt in node.statements:
                self._generate_statement(stmt)
            return None

        elif isinstance(node, ExprStmtNode):
            return self._generate_expression(node.expression)

        elif isinstance(node, VarDeclStmtNode):
            return self._generate_var_decl(node)

        elif isinstance(node, IfStmtNode):
            return self._generate_if(node)

        elif isinstance(node, WhileStmtNode):
            return self._generate_while(node)

        elif isinstance(node, ForStmtNode):
            return self._generate_for(node)

        elif isinstance(node, ReturnStmtNode):
            return self._generate_return(node)

        return None

    def _generate_var_decl(self, node: VarDeclStmtNode) -> Optional[Operand]:
        if not self.current_function:
            return None

        symbol = self.current_function.lookup_symbol(node.name)
        if not symbol:
            return None

        if node.initializer:
            value = self._generate_expression(node.initializer)
            if value:
                addr_temp = symbol.get("address_temp")
                if addr_temp:
                    self.current_block.add_instruction(
                        store(memory(addr_temp), value,
                              line=node.line, comment=f"{node.name} = ...")
                    )

        return None

    def _generate_if(self, node: IfStmtNode) -> None:
        func = self.current_function
        if not func:
            return

        then_label = func.new_label("L_then")
        else_label = func.new_label("L_else") if node.else_branch else None
        end_label = func.new_label("L_endif")

        cond = self._generate_expression(node.condition)

        if cond:
            if else_label:
                self.current_block.add_instruction(
                    jump_if_not(cond, else_label, line=node.condition.line)
                )
            else:
                self.current_block.add_instruction(
                    jump_if_not(cond, end_label, line=node.condition.line)
                )

        then_block = func.create_block(then_label.name)
        self.current_block.add_successor(then_block)
        self.current_block = then_block

        self._generate_statement(node.then_branch)

        if not self.current_block.is_terminated():
            self.current_block.add_instruction(jump(end_label))

        if node.else_branch and else_label:
            else_block = func.create_block(else_label.name)
            self.current_block.add_successor(else_block)
            self.current_block = else_block

            self._generate_statement(node.else_branch)

            if not self.current_block.is_terminated():
                self.current_block.add_instruction(jump(end_label))

        end_block = func.create_block(end_label.name)
        if else_label:
            func.get_block(else_label.name).add_successor(end_block)
        func.get_block(then_label.name).add_successor(end_block)
        self.current_block = end_block


    def _generate_while(self, node: WhileStmtNode) -> None:
        func = self.current_function
        if not func:
            return

        header_label = func.new_label("L_while_header")
        body_label = func.new_label("L_while_body")
        end_label = func.new_label("L_while_end")

        self.current_block.add_instruction(jump(header_label))

        header_block = func.create_block(header_label.name, BlockType.LOOP_HEADER)
        self.current_block.add_successor(header_block)
        self.current_block = header_block

        cond = self._generate_expression(node.condition)
        if cond:
            self.current_block.add_instruction(
                jump_if_not(cond, end_label, line=node.condition.line)
            )
        self.current_block.add_successor(func.create_block(body_label.name))

        body_block = func.get_block(body_label.name)
        body_block.block_type = BlockType.NORMAL
        self.current_block = body_block

        self._generate_statement(node.body)

        if not self.current_block.is_terminated():
            self.current_block.add_instruction(jump(header_label))
            latch_block = self.current_block
            latch_block.block_type = BlockType.LOOP_LATCH
            header_block.predecessors.add(latch_block)

        end_block = func.create_block(end_label.name)
        header_block.add_successor(end_block)
        self.current_block = end_block

    def _generate_for(self, node: ForStmtNode) -> None:

        if node.init:
            self._generate_statement(node.init)

        from src.parser.ast import WhileStmtNode
        while_node = WhileStmtNode(node.condition, node.body)
        self._generate_while(while_node)


        if node.update:
            pass

    def _generate_return(self, node: ReturnStmtNode) -> Optional[Operand]:
        if node.value:
            value = self._generate_expression(node.value)
            self.current_block.add_instruction(
                ret(value, line=node.line)
            )
        else:
            self.current_block.add_instruction(ret(line=node.line))
        return None

    def _generate_expression(self, node: ExpressionNode) -> Optional[Operand]:
        if isinstance(node, LiteralExprNode):
            return literal(node.value, node.literal_type)

        elif isinstance(node, IdentifierExprNode):
            return self._load_identifier(node)

        elif isinstance(node, BinaryExprNode):
            return self._generate_binary(node)

        elif isinstance(node, UnaryExprNode):
            return self._generate_unary(node)

        elif isinstance(node, CallExprNode):
            return self._generate_call(node)

        elif isinstance(node, AssignmentExprNode):
            return self._generate_assignment(node)

        return None

    def _load_identifier(self, node: IdentifierExprNode) -> Optional[Operand]:
        if not self.current_function:
            return var(node.name)

        symbol = self.current_function.lookup_symbol(node.name)
        if not symbol:
            return var(node.name)

        if symbol.get("is_parameter"):
            return var(node.name, symbol["type"])

        addr_temp = symbol.get("address_temp")
        if addr_temp:
            result = self.current_function.new_temp(symbol["type"])
            self.current_block.add_instruction(
                load(result, memory(addr_temp),
                     line=node.line, comment=f"load {node.name}")
            )
            return result

        return var(node.name, symbol["type"])

    def _generate_binary(self, node: BinaryExprNode) -> Optional[Operand]:
        left = self._generate_expression(node.left)
        right = self._generate_expression(node.right)

        if not left or not right:
            return None

        result = self.current_function.new_temp()

        op_map = {
            "+": InstructionType.ADD,
            "-": InstructionType.SUB,
            "*": InstructionType.MUL,
            "/": InstructionType.DIV,
            "%": InstructionType.MOD,
            "&&": InstructionType.AND,
            "||": InstructionType.OR,
            "==": InstructionType.CMP_EQ,
            "!=": InstructionType.CMP_NE,
            "<": InstructionType.CMP_LT,
            "<=": InstructionType.CMP_LE,
            ">": InstructionType.CMP_GT,
            ">=": InstructionType.CMP_GE,
        }

        op_type = op_map.get(node.operator)
        if not op_type:
            return None

        from src.ir.instructions import BinaryArithInst, BinaryLogicInst, CmpInst

        if op_type in (InstructionType.AND, InstructionType.OR):
            inst = BinaryLogicInst(
                dest=result,
                src1=left,
                src2=right,
                op=op_type,
                line=node.line,
                comment=node.operator
            )
        elif op_type.name.startswith("CMP"):
            inst = CmpInst(
                dest=result,
                src1=left,
                src2=right,
                cmp_type=op_type,
                line=node.line,
                comment=node.operator
            )
        else:
            inst = BinaryArithInst(
                dest=result,
                src1=left,
                src2=right,
                op=op_type,
                line=node.line,
                comment=node.operator
            )

        self.current_block.add_instruction(inst)
        return result

    def _generate_unary(self, node: UnaryExprNode) -> Optional[Operand]:
        operand = self._generate_expression(node.operand)
        if not operand:
            return None

        result = self.current_function.new_temp()

        from src.ir.instructions import UnaryArithInst, UnaryLogicInst, InstructionType

        if node.operator == '-':
            inst = UnaryArithInst(
                dest=result,
                src=operand,
                op=InstructionType.NEG,
                line=node.line,
                comment="-"
            )
        elif node.operator == '!':
            inst = UnaryLogicInst(
                dest=result,
                src=operand,
                line=node.line,
                comment="!"
            )
        else:
            return None

        self.current_block.add_instruction(inst)
        return result

    def _generate_call(self, node: CallExprNode) -> Optional[Operand]:
        arg_operands = []
        for arg in node.arguments:
            arg_val = self._generate_expression(arg)
            if arg_val:
                arg_operands.append(arg_val)

        symbol = self.symbol_table.lookup(node.callee)
        return_type_str = "void"
        if symbol:
            if hasattr(symbol, 'return_type') and symbol.return_type:
                return_type_str = str(symbol.return_type)
            elif hasattr(symbol, 'symbol_type') and hasattr(symbol.symbol_type, 'return_type'):
                return_type_str = str(symbol.symbol_type.return_type)

        result = None
        if return_type_str != "void":
            result = self.current_function.new_temp(return_type_str)

        self.current_block.add_instruction(
            CallInst(dest=result, func_name=node.callee, arguments=arg_operands,
                     line=node.line, comment=f"call {node.callee}")
        )

        return result

    def _generate_assignment(self, node: AssignmentExprNode) -> Optional[Operand]:
        value = self._generate_expression(node.value)
        if not value:
            return None

        if isinstance(node.target, IdentifierExprNode):
            target_name = node.target.name

            if self.current_function:
                symbol = self.current_function.lookup_symbol(target_name)
                if symbol and not symbol.get("is_parameter"):
                    addr_temp = symbol.get("address_temp")
                    if addr_temp:
                        self.current_block.add_instruction(
                            store(memory(addr_temp), value,
                                  line=node.line, comment=f"{target_name} = ...")
                        )
                        return value
                self.current_block.add_instruction(
                    store(memory(var(target_name)), value,
                          line=node.line, comment=f"{target_name} = ...")
                )
                return value
            else:
                self.current_block.add_instruction(
                    store(memory(var(target_name, is_global=True)), value,
                          line=node.line, comment=f"{target_name} = ...")
                )
                return value

        return None

    def get_function_ir(self, name: str) -> Optional[FunctionIR]:
        return self.program_ir.get_function(name)

    def get_all_ir(self) -> ProgramIR:
        return self.program_ir

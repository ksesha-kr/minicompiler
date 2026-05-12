from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Union
from enum import Enum, auto

from src.ir.operand import Operand, TempOperand, VarOperand, LiteralOperand, LabelOperand, MemoryOperand


class InstructionType(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()

    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()

    CMP_EQ = auto()
    CMP_NE = auto()
    CMP_LT = auto()
    CMP_LE = auto()
    CMP_GT = auto()
    CMP_GE = auto()

    LOAD = auto()
    STORE = auto()
    ALLOCA = auto()
    GEP = auto()

    JUMP = auto()
    JUMP_IF = auto()
    JUMP_IF_NOT = auto()
    LABEL = auto()
    PHI = auto()

    CALL = auto()
    RETURN = auto()
    PARAM = auto()


@dataclass
class Instruction(ABC):

    line: int = 0
    comment: Optional[str] = None

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @property
    @abstractmethod
    def type(self) -> InstructionType:
        pass

    def with_comment(self, comment: str) -> 'Instruction':
        self.comment = comment
        return self


@dataclass(kw_only=True)
class BinaryArithInst(Instruction):

    dest: TempOperand
    src1: Operand
    src2: Operand
    op: InstructionType

    def __str__(self) -> str:
        op_name = self.op.name
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = {op_name} {self.src1}, {self.src2}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": self.op.name,
            "dest": self.dest.to_dict(),
            "src1": self.src1.to_dict(),
            "src2": self.src2.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return self.op


@dataclass(kw_only=True)
class UnaryArithInst(Instruction):

    dest: TempOperand
    src: Operand
    op: InstructionType

    def __str__(self) -> str:
        op_name = self.op.name
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = {op_name} {self.src}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": self.op.name,
            "dest": self.dest.to_dict(),
            "src": self.src.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return self.op



@dataclass(kw_only=True)
class BinaryLogicInst(Instruction):

    dest: TempOperand
    src1: Operand
    src2: Operand
    op: InstructionType

    def __str__(self) -> str:
        op_name = self.op.name
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = {op_name} {self.src1}, {self.src2}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": self.op.name,
            "dest": self.dest.to_dict(),
            "src1": self.src1.to_dict(),
            "src2": self.src2.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return self.op


@dataclass(kw_only=True)
class UnaryLogicInst(Instruction):

    dest: TempOperand
    src: Operand

    def __str__(self) -> str:
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = NOT {self.src}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "NOT",
            "dest": self.dest.to_dict(),
            "src": self.src.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.NOT



@dataclass(kw_only=True)
class CmpInst(Instruction):

    dest: TempOperand
    src1: Operand
    src2: Operand
    cmp_type: InstructionType

    def __str__(self) -> str:
        op_map = {
            InstructionType.CMP_EQ: "==",
            InstructionType.CMP_NE: "!=",
            InstructionType.CMP_LT: "<",
            InstructionType.CMP_LE: "<=",
            InstructionType.CMP_GT: ">",
            InstructionType.CMP_GE: ">=",
        }
        op = op_map.get(self.cmp_type, "?")
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = CMP_{op} {self.src1}, {self.src2}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": self.cmp_type.name,
            "dest": self.dest.to_dict(),
            "src1": self.src1.to_dict(),
            "src2": self.src2.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return self.cmp_type



@dataclass(kw_only=True)
class LoadInst(Instruction):

    dest: TempOperand
    addr: Operand

    def __str__(self) -> str:
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = LOAD {self.addr}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "LOAD",
            "dest": self.dest.to_dict(),
            "addr": self.addr.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.LOAD


@dataclass(kw_only=True)
class StoreInst(Instruction):

    addr: Operand
    src: Operand

    def __str__(self) -> str:
        comment = f" # {self.comment}" if self.comment else ""
        return f"  STORE {self.addr}, {self.src}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "STORE",
            "addr": self.addr.to_dict(),
            "src": self.src.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.STORE


@dataclass(kw_only=True)
class AllocaInst(Instruction):

    dest: TempOperand
    size: int
    type_hint: Optional[str] = None

    def __str__(self) -> str:
        comment = f" # {self.comment}" if self.comment else ""
        type_info = f":{self.type_hint}" if self.type_hint else ""
        return f"  {self.dest} = ALLOCA {self.size}{type_info}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "ALLOCA",
            "dest": self.dest.to_dict(),
            "size": self.size,
            "type_hint": self.type_hint,
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.ALLOCA



@dataclass(kw_only=True)
class JumpInst(Instruction):

    target: LabelOperand

    def __str__(self) -> str:
        comment = f" # {self.comment}" if self.comment else ""
        return f"  JUMP {self.target}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "JUMP",
            "target": self.target.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.JUMP


@dataclass(kw_only=True)
class CondJumpInst(Instruction):

    condition: TempOperand
    target: LabelOperand
    invert: bool = False

    def __str__(self) -> str:
        op = "JUMP_IF_NOT" if self.invert else "JUMP_IF"
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {op} {self.condition}, {self.target}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "JUMP_IF_NOT" if self.invert else "JUMP_IF",
            "condition": self.condition.to_dict(),
            "target": self.target.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.JUMP_IF_NOT if self.invert else InstructionType.JUMP_IF


@dataclass(kw_only=True)
class LabelInst(Instruction):

    name: LabelOperand

    def __str__(self) -> str:
        return f"{self.name}:"

    def to_dict(self) -> dict:
        return {
            "type": "LABEL",
            "name": self.name.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.LABEL


@dataclass(kw_only=True)
class PhiInst(Instruction):

    dest: TempOperand
    values: List[tuple[Operand, LabelOperand]]

    def __str__(self) -> str:
        pairs = ", ".join(f"({v}, {b})" for v, b in self.values)
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {self.dest} = PHI {pairs}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "PHI",
            "dest": self.dest.to_dict(),
            "values": [(v.to_dict(), b.to_dict()) for v, b in self.values],
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.PHI



@dataclass(kw_only=True)
class CallInst(Instruction):

    dest: Optional[TempOperand]
    func_name: str
    arguments: List[Operand]

    def __str__(self) -> str:
        args = ", ".join(str(a) for a in self.arguments)
        dest_part = f"{self.dest} = " if self.dest else ""
        comment = f" # {self.comment}" if self.comment else ""
        return f"  {dest_part}CALL {self.func_name}({args}){comment}"

    def to_dict(self) -> dict:
        return {
            "type": "CALL",
            "dest": self.dest.to_dict() if self.dest else None,
            "func": self.func_name,
            "arguments": [a.to_dict() for a in self.arguments],
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.CALL


@dataclass(kw_only=True)
class ReturnInst(Instruction):

    value: Optional[Operand] = None

    def __str__(self) -> str:
        value_part = f" {self.value}" if self.value else ""
        comment = f" # {self.comment}" if self.comment else ""
        return f"  RETURN{value_part}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "RETURN",
            "value": self.value.to_dict() if self.value else None,
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.RETURN


@dataclass(kw_only=True)
class ParamInst(Instruction):

    index: int
    value: Operand

    def __str__(self) -> str:
        comment = f" # {self.comment}" if self.comment else ""
        return f"  PARAM {self.index}, {self.value}{comment}"

    def to_dict(self) -> dict:
        return {
            "type": "PARAM",
            "index": self.index,
            "value": self.value.to_dict(),
            "line": self.line,
            "comment": self.comment
        }

    @property
    def type(self) -> InstructionType:
        return InstructionType.PARAM



def add(dest: TempOperand, src1: Operand, src2: Operand,
        line: int = 0, comment: str = None) -> BinaryArithInst:
    return BinaryArithInst(dest=dest, src1=src1, src2=src2, op=InstructionType.ADD, line=line, comment=comment)

def sub(dest: TempOperand, src1: Operand, src2: Operand,
        line: int = 0, comment: str = None) -> BinaryArithInst:
    return BinaryArithInst(dest=dest, src1=src1, src2=src2, op=InstructionType.SUB, line=line, comment=comment)

def mul(dest: TempOperand, src1: Operand, src2: Operand,
        line: int = 0, comment: str = None) -> BinaryArithInst:
    return BinaryArithInst(dest=dest, src1=src1, src2=src2, op=InstructionType.MUL, line=line, comment=comment)

def div(dest: TempOperand, src1: Operand, src2: Operand,
        line: int = 0, comment: str = None) -> BinaryArithInst:
    return BinaryArithInst(dest=dest, src1=src1, src2=src2, op=InstructionType.DIV, line=line, comment=comment)

def cmp_eq(dest: TempOperand, src1: Operand, src2: Operand,
           line: int = 0, comment: str = None) -> CmpInst:
    return CmpInst(dest=dest, src1=src1, src2=src2, cmp_type=InstructionType.CMP_EQ, line=line, comment=comment)

def cmp_lt(dest: TempOperand, src1: Operand, src2: Operand,
           line: int = 0, comment: str = None) -> CmpInst:
    return CmpInst(dest=dest, src1=src1, src2=src2, cmp_type=InstructionType.CMP_LT, line=line, comment=comment)

def load(dest: TempOperand, addr: Operand,
         line: int = 0, comment: str = None) -> LoadInst:
    return LoadInst(dest=dest, addr=addr, line=line, comment=comment)

def store(addr: Operand, src: Operand,
          line: int = 0, comment: str = None) -> StoreInst:
    return StoreInst(addr=addr, src=src, line=line, comment=comment)

def jump(target: LabelOperand,
         line: int = 0, comment: str = None) -> JumpInst:
    return JumpInst(target=target, line=line, comment=comment)

def jump_if(cond: TempOperand, target: LabelOperand,
            line: int = 0, comment: str = None) -> CondJumpInst:
    return CondJumpInst(condition=cond, target=target, invert=False, line=line, comment=comment)

def jump_if_not(cond: TempOperand, target: LabelOperand,
                line: int = 0, comment: str = None) -> CondJumpInst:
    return CondJumpInst(condition=cond, target=target, invert=True, line=line, comment=comment)

def label(name: LabelOperand,
          line: int = 0, comment: str = None) -> LabelInst:
    return LabelInst(name=name, line=line, comment=comment)

def call(dest: Optional[TempOperand], func_name: str, arguments: List[Operand],
         line: int = 0, comment: str = None) -> CallInst:
    return CallInst(dest=dest, func_name=func_name, arguments=arguments, line=line, comment=comment)

def ret(value: Optional[Operand] = None,
        line: int = 0, comment: str = None) -> ReturnInst:
    return ReturnInst(value=value, line=line, comment=comment)
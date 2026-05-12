from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Union, List
from enum import Enum, auto


class OperandType(Enum):
    TEMPORARY = auto()
    VARIABLE = auto()
    LITERAL = auto()
    LABEL = auto()
    MEMORY = auto()


@dataclass(frozen=True)
class Operand(ABC):

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


@dataclass(frozen=True)
class TempOperand(Operand):

    index: int
    type_hint: Optional[str] = None

    def __str__(self) -> str:
        return f"t{self.index}"

    def to_dict(self) -> dict:
        return {
            "kind": "temporary",
            "index": self.index,
            "type": self.type_hint
        }


@dataclass(frozen=True)
class VarOperand(Operand):

    name: str
    type_hint: Optional[str] = None
    is_global: bool = False
    offset: Optional[int] = None

    def __str__(self) -> str:
        suffix = ""
        if self.offset is not None:
            suffix = f"_off{self.offset}"
        return f"{self.name}{suffix}"

    def to_dict(self) -> dict:
        return {
            "kind": "variable",
            "name": self.name,
            "type": self.type_hint,
            "is_global": self.is_global,
            "offset": self.offset
        }


@dataclass(frozen=True)
class LiteralOperand(Operand):

    value: Union[int, float, bool, str]
    literal_type: str

    def __str__(self) -> str:
        if self.literal_type == "string":
            return f'"{self.value}"'
        elif self.literal_type == "bool":
            return "true" if self.value else "false"
        return str(self.value)

    def to_dict(self) -> dict:
        return {
            "kind": "literal",
            "value": self.value,
            "type": self.literal_type
        }


@dataclass(frozen=True)
class LabelOperand(Operand):

    name: str

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> dict:
        return {
            "kind": "label",
            "name": self.name
        }


@dataclass(frozen=True)
class MemoryOperand(Operand):

    base: Operand
    offset: int = 0

    def __str__(self) -> str:
        if self.offset == 0:
            return f"[{self.base}]"
        return f"[{self.base}+{self.offset}]"

    def to_dict(self) -> dict:
        return {
            "kind": "memory",
            "base": self.base.to_dict(),
            "offset": self.offset
        }


def temp(index: int, type_hint: Optional[str] = None) -> TempOperand:
    return TempOperand(index, type_hint)


def var(name: str, type_hint: Optional[str] = None,
        is_global: bool = False, offset: Optional[int] = None) -> VarOperand:
    return VarOperand(name, type_hint, is_global, offset)


def literal(value: Union[int, float, bool, str],
            literal_type: str) -> LiteralOperand:
    return LiteralOperand(value, literal_type)


def label(name: str) -> LabelOperand:
    return LabelOperand(name)


def memory(base: Operand, offset: int = 0) -> MemoryOperand:
    return MemoryOperand(base, offset)
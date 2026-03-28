from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field


class Type(ABC):

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def is_compatible_with(self, other: 'Type') -> bool:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


@dataclass(frozen=True)
class BaseType(Type):

    name: str

    VALID_TYPES = frozenset(['int', 'float', 'bool', 'void', 'string'])

    def __post_init__(self):
        if self.name not in self.VALID_TYPES:
            raise ValueError(f"Недопустимый базовый тип: {self.name}")

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        return isinstance(other, BaseType) and self.name == other.name

    def is_compatible_with(self, other: Type) -> bool:
        if not isinstance(other, BaseType):
            return False

        if self.name == other.name:
            return True

        if self.name == 'float' and other.name == 'int':
            return True

        return False

    def to_dict(self) -> dict:
        return {
            "kind": "base",
            "name": self.name
        }


@dataclass
class StructType(Type):

    name: str
    fields: Dict[str, Type] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"struct {self.name}"

    def __eq__(self, other) -> bool:
        return isinstance(other, StructType) and self.name == other.name

    def is_compatible_with(self, other: Type) -> bool:
        return self == other

    def get_field_type(self, field_name: str) -> Optional[Type]:
        return self.fields.get(field_name)

    def to_dict(self) -> dict:
        return {
            "kind": "struct",
            "name": self.name,
            "fields": {name: t.to_dict() for name, t in self.fields.items()}
        }


@dataclass(frozen=True)
class FunctionType(Type):

    return_type: Type
    param_types: List[Type] = field(default_factory=list)

    def __str__(self) -> str:
        params = ", ".join(str(t) for t in self.param_types)
        return f"fn({params}) -> {self.return_type}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return (self.return_type == other.return_type and
                self.param_types == other.param_types)

    def is_compatible_with(self, other: Type) -> bool:
        return self == other

    def to_dict(self) -> dict:
        return {
            "kind": "function",
            "return_type": self.return_type.to_dict(),
            "param_types": [t.to_dict() for t in self.param_types]
        }

TYPE_INT = BaseType('int')
TYPE_FLOAT = BaseType('float')
TYPE_BOOL = BaseType('bool')
TYPE_VOID = BaseType('void')
TYPE_STRING = BaseType('string')

TYPE_REGISTRY: Dict[str, Type] = {
    'int': TYPE_INT,
    'float': TYPE_FLOAT,
    'bool': TYPE_BOOL,
    'void': TYPE_VOID,
    'string': TYPE_STRING,
}


def parse_type(type_name: str) -> Type:
    if type_name in TYPE_REGISTRY:
        return TYPE_REGISTRY[type_name]
    return StructType(type_name)
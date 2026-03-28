from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto

from src.semantic.types import Type, TYPE_VOID


class SymbolKind(Enum):
    VARIABLE = auto()
    PARAMETER = auto()
    FUNCTION = auto()
    STRUCT = auto()


@dataclass
class SymbolInfo:

    name: str
    symbol_type: Type
    kind: SymbolKind
    line: int
    column: int
    scope_level: int = 0

    return_type: Optional[Type] = None
    parameters: List['SymbolInfo'] = field(default_factory=list)

    fields: Dict[str, 'SymbolInfo'] = field(default_factory=dict)

    is_initialized: bool = False

    def to_dict(self) -> dict:
        result = {
            "name": self.name,
            "type": self.symbol_type.to_dict() if self.symbol_type else None,
            "kind": self.kind.name,
            "line": self.line,
            "column": self.column,
            "scope_level": self.scope_level,
            "initialized": self.is_initialized
        }

        if self.kind == SymbolKind.FUNCTION:
            result["return_type"] = self.return_type.to_dict() if self.return_type else None
            result["parameters"] = [p.to_dict() for p in self.parameters]

        if self.kind == SymbolKind.STRUCT:
            result["fields"] = {n: f.to_dict() for n, f in self.fields.items()}

        return result


class Scope:

    def __init__(self, name: str, level: int, parent: Optional['Scope'] = None):
        self.name = name
        self.level = level
        self.parent = parent
        self.symbols: Dict[str, SymbolInfo] = {}

    def insert(self, symbol: SymbolInfo) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        return self.symbols.get(name)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "symbols": {name: sym.to_dict() for name, sym in self.symbols.items()}
        }


class SymbolTable:

    def __init__(self):
        self._global_scope = Scope("global", 0)
        self._current_scope = self._global_scope
        self._all_scopes = [self._global_scope]

    @property
    def current_scope(self) -> Scope:
        return self._current_scope

    @property
    def scope_depth(self) -> int:
        return self._current_scope.level

    def enter_scope(self, name: str = "block") -> None:
        new_scope = Scope(name, self._current_scope.level + 1, self._current_scope)
        self._current_scope = new_scope
        self._all_scopes.append(new_scope)

    def exit_scope(self) -> None:
        if self._current_scope.parent is not None:
            self._current_scope = self._current_scope.parent

    def insert(self, name: str, symbol_info: SymbolInfo) -> bool:
        return self._current_scope.insert(symbol_info)

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        scope = self._current_scope
        while scope is not None:
            symbol = scope.lookup(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None

    def lookup_local(self, name: str) -> Optional[SymbolInfo]:
        return self._current_scope.lookup(name)

    def mark_initialized(self, name: str) -> bool:
        symbol = self.lookup(name)
        if symbol and symbol.kind in (SymbolKind.VARIABLE, SymbolKind.PARAMETER):
            symbol.is_initialized = True
            return True
        return False

    def is_initialized(self, name: str) -> bool:
        symbol = self.lookup(name)
        return symbol.is_initialized if symbol else False

    def get_all_symbols(self) -> Dict[str, List[SymbolInfo]]:
        result = {}

        def collect(scope: Scope):
            if scope.name not in result:
                result[scope.name] = []
            result[scope.name].extend(scope.symbols.values())

        collect(self._global_scope)
        return result

    def to_dict(self) -> dict:

        def scope_to_tree(scope: Scope) -> dict:
            result = scope.to_dict()
            return result

        return scope_to_tree(self._global_scope)

    def dump(self, indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent

        for scope in self._all_scopes:
            lines.append(f"{prefix}Scope: {scope.name} (level {scope.level})")
            for name, sym in scope.symbols.items():
                if sym.kind == SymbolKind.FUNCTION:
                    params = ", ".join(f"{p.name}: {p.symbol_type}" for p in sym.parameters)
                    lines.append(f"{prefix}  {name}: fn({params}) -> {sym.return_type} function [line {sym.line}]")
                elif sym.kind == SymbolKind.STRUCT:
                    fields = ", ".join(f"{f.name}: {f.symbol_type}" for f in sym.fields.values())
                    lines.append(f"{prefix}  {name}: struct {{{fields}}} [line {sym.line}]")
                else:
                    init_status = " = init" if sym.is_initialized else ""
                    lines.append(
                        f"{prefix}  {name}: {sym.symbol_type} {sym.kind.name.lower()}{init_status} [line {sym.line}]")

        return "\n".join(lines)
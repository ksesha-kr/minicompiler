from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum, auto


class SemanticErrorKind(Enum):
    UNDECLARED_IDENTIFIER = auto()
    DUPLICATE_DECLARATION = auto()
    TYPE_MISMATCH = auto()
    ARGUMENT_COUNT_MISMATCH = auto()
    ARGUMENT_TYPE_MISMATCH = auto()
    INVALID_RETURN_TYPE = auto()
    INVALID_CONDITION_TYPE = auto()
    USE_BEFORE_DECLARATION = auto()
    INVALID_ASSIGNMENT_TARGET = auto()
    UNINITIALIZED_USE = auto()
    INVALID_FIELD_ACCESS = auto()
    VOID_VALUE_USED = auto()


@dataclass
class SemanticError:

    kind: SemanticErrorKind
    message: str
    filename: str
    line: int
    column: int
    context: Optional[str] = None
    expected: Optional[str] = None
    found: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        lines = []

        error_name = self.kind.name.replace('_', ' ').lower()
        lines.append(f"semantic error: {error_name}")
        lines.append(f"  --> {self.filename}:{self.line}:{self.column}")

        if self.context:
            lines.append(f"   |")
            lines.append(f"{self.context}")
            lines.append(f"   |")

        if self.expected or self.found:
            if self.expected:
                lines.append(f"   = expected: {self.expected}")
            if self.found:
                lines.append(f"   = found: {self.found}")

        if self.suggestion:
            lines.append(f"   = note: {self.suggestion}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        result = {
            "kind": self.kind.name,
            "message": self.message,
            "location": {
                "file": self.filename,
                "line": self.line,
                "column": self.column
            }
        }

        if self.context:
            result["context"] = self.context
        if self.expected:
            result["expected"] = self.expected
        if self.found:
            result["found"] = self.found
        if self.suggestion:
            result["suggestion"] = self.suggestion

        return result


class SemanticErrorCollector:

    def __init__(self, filename: str = "<unknown>"):
        self.filename = filename
        self.errors: List[SemanticError] = []
        self._max_errors = 100

    def add_error(self, error: SemanticError) -> None:
        if len(self.errors) < self._max_errors:
            self.errors.append(error)

    def error(self, kind: SemanticErrorKind, message: str,
              line: int, column: int, **kwargs) -> None:
        error = SemanticError(
            kind=kind,
            message=message,
            filename=self.filename,
            line=line,
            column=column,
            **kwargs
        )
        self.add_error(error)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_errors(self) -> List[SemanticError]:
        return self.errors.copy()

    def __str__(self) -> str:
        if not self.errors:
            return "No semantic errors."

        lines = [f"Found {len(self.errors)} semantic error(s):\n"]
        for error in self.errors:
            lines.append(str(error))
            lines.append("")
        return "\n".join(lines)
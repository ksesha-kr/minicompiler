from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum, auto

from src.ir.basic_block import ControlFlowGraph, BasicBlock, BlockType
from src.ir.operand import (
    TempOperand, VarOperand, LiteralOperand, Operand, LabelOperand,
    temp, var, literal, label
)
from src.ir.instructions import Instruction, AllocaInst, ParamInst


@dataclass(kw_only=True)
class FunctionIR:

    name: str
    return_type: str
    parameters: List[tuple[str, str]]
    cfg: ControlFlowGraph = field(default_factory=lambda: ControlFlowGraph(""))

    symbol_map: Dict[str, dict] = field(default_factory=dict)

    temp_counter: int = 0
    label_counter: int = 0
    stack_offset: int = 0

    def __post_init__(self):
        self.cfg.name = self.name

    def get_block(self, label_name: str) -> Optional[BasicBlock]:
        return self.cfg.get_block(label_name)

    def create_block(self, label_name: str, block_type: BlockType = BlockType.NORMAL) -> BasicBlock:
        return self.cfg.create_block(label_name, block_type)

    def new_temp(self, type_hint: Optional[str] = None) -> TempOperand:
        self.temp_counter += 1
        return temp(self.temp_counter, type_hint)

    def new_label(self, prefix: str = "L") -> LabelOperand:
        self.label_counter += 1
        from src.ir.operand import label
        return label(f"{prefix}{self.label_counter}")

    def allocate_local(self, name: str, var_type: str, size: int = 4) -> VarOperand:
        var_op = var(name, var_type, is_global=False, offset=self.stack_offset)
        self.symbol_map[name] = {
            "type": var_type,
            "is_parameter": False,
            "offset": self.stack_offset,
            "size": size
        }
        self.stack_offset += size
        return var_op

    def register_parameter(self, name: str, param_type: str, index: int) -> VarOperand:
        var_op = var(name, param_type, is_global=False, offset=None)
        self.symbol_map[name] = {
            "type": param_type,
            "is_parameter": True,
            "index": index,
            "offset": None
        }
        return var_op

    def lookup_symbol(self, name: str) -> Optional[dict]:
        return self.symbol_map.get(name)

    def generate_prologue(self, entry_block: BasicBlock) -> None:
        for name, info in self.symbol_map.items():
            if not info.get("is_parameter"):
                temp_var = self.new_temp(info["type"])
                entry_block.add_instruction(
                    AllocaInst(
                        dest=temp_var,
                        size=info.get("size", 4),
                        type_hint=info.get("type")
                    )
                )
                info["address_temp"] = temp_var

    def __str__(self) -> str:
        params = ", ".join(f"{t} {n}" for n, t in self.parameters)
        lines = [f"function {self.name}: {self.return_type} ({params})"]
        lines.append(str(self.cfg))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "return_type": self.return_type,
            "parameters": self.parameters,
            "cfg": self.cfg.to_dict(),
            "symbols": self.symbol_map,
            "temp_count": self.temp_counter,
            "label_count": self.label_counter
        }


@dataclass
class ProgramIR:

    functions: Dict[str, FunctionIR] = field(default_factory=dict)
    global_vars: Dict[str, dict] = field(default_factory=dict)

    def add_function(self, func: FunctionIR) -> None:
        self.functions[func.name] = func

    def get_function(self, name: str) -> Optional[FunctionIR]:
        return self.functions.get(name)

    def __str__(self) -> str:
        lines = []
        if self.global_vars:
            lines.append("# Global variables")
            for name, info in self.global_vars.items():
                lines.append(f".global {name}  # {info.get('type', 'unknown')}")
            lines.append("")

        for func in self.functions.values():
            lines.append(str(func))
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "functions": {name: f.to_dict() for name, f in self.functions.items()},
            "globals": self.global_vars
        }

    def get_statistics(self) -> dict:
        stats = {
            "function_count": len(self.functions),
            "global_var_count": len(self.global_vars),
            "total_blocks": 0,
            "total_instructions": 0,
            "instruction_types": {},
            "total_temps": 0,
            "total_labels": 0
        }

        for func in self.functions.values():
            stats["total_blocks"] += len(func.cfg.blocks)
            stats["total_temps"] += func.temp_counter
            stats["total_labels"] += func.label_counter

            for block in func.cfg.blocks.values():
                for inst in block.instructions:
                    inst_type = inst.type.name
                    stats["total_instructions"] += 1
                    stats["instruction_types"][inst_type] = \
                        stats["instruction_types"].get(inst_type, 0) + 1

        return stats
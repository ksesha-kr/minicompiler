from typing import Optional
import json

from src.ir.function import ProgramIR, FunctionIR
from src.ir.basic_block import BasicBlock


class IROutput:

    @staticmethod
    def to_text(ir: ProgramIR, source_file: str = None) -> str:
        lines = []

        if source_file:
            lines.append(f"# Program: {source_file}")
            lines.append("# Generated IR")
            lines.append("")

        if ir.global_vars:
            lines.append("# Global variables")
            for name, info in ir.global_vars.items():
                init = " = <init>" if info.get("initialized") else ""
                lines.append(f".global {name}: {info.get('type', 'unknown')}{init}")
            lines.append("")

        # Функции
        for func in ir.functions.values():
            lines.append(IROutput._function_to_text(func))
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _function_to_text(func: FunctionIR) -> str:
        params = ", ".join(f"{t} {n}" for n, t in func.parameters)
        lines = [f"function {func.name}: {func.return_type} ({params})"]

        for block in func.cfg.get_blocks_in_order():
            lines.append(f"  {block.label}:")
            for inst in block.instructions:
                lines.append(f"    {str(inst).lstrip()}")

        return "\n".join(lines)

    @staticmethod
    def to_dot(ir: ProgramIR, function_name: str = None) -> str:
        lines = ["digraph CFG {", "  rankdir=TB;", "  node [shape=box];", ""]

        functions = [ir.functions[function_name]] if function_name else ir.functions.values()

        for func in functions:
            if function_name:
                lines.append(f'  // CFG for {func.name}')

            for block in func.cfg.blocks.values():
                label_lines = [block.label.name]
                if block.block_type.name != "NORMAL":
                    label_lines.append(f"[{block.block_type.name}]")

                for inst in block.instructions[:5]:
                    inst_str = str(inst).strip()
                    if len(inst_str) > 40:
                        inst_str = inst_str[:37] + "..."
                    label_lines.append(inst_str)

                if len(block.instructions) > 5:
                    label_lines.append(f"... ({len(block.instructions)} total)")

                label = "\\n".join(label_lines)

                colors = {
                    "ENTRY": "lightgreen",
                    "EXIT": "lightcoral",
                    "LOOP_HEADER": "lightyellow",
                    "LOOP_LATCH": "khaki",
                    "NORMAL": "white"
                }
                color = colors.get(block.block_type.name, "white")

                lines.append(f'  "{block.label.name}" [label="{label}", style=filled, fillcolor={color}];')

                for succ in block.successors:
                    lines.append(f'  "{block.label.name}" -> "{succ.label.name}";')

            lines.append("")

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def to_json(ir: ProgramIR) -> str:
        return json.dumps(ir.to_dict(), indent=2, ensure_ascii=False)

    @staticmethod
    def get_statistics(ir: ProgramIR) -> str:
        stats = ir.get_statistics()

        lines = [
            "IR Statistics:",
            f"  Functions: {stats['function_count']}",
            f"  Global variables: {stats['global_var_count']}",
            f"  Basic blocks: {stats['total_blocks']}",
            f"  Instructions: {stats['total_instructions']}",
            f"  Temporaries: {stats['total_temps']}",
            f"  Labels: {stats['total_labels']}",
            "",
            "Instructions by type:"
        ]

        for inst_type, count in sorted(stats['instruction_types'].items()):
            lines.append(f"  {inst_type}: {count}")

        return "\n".join(lines)
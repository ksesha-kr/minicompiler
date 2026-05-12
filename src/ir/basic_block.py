from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum, auto

from src.ir.instructions import Instruction, LabelInst, JumpInst, CondJumpInst, ReturnInst
from src.ir.operand import LabelOperand


class BlockType(Enum):
    ENTRY = auto()
    NORMAL = auto()
    EXIT = auto()
    LOOP_HEADER = auto()
    LOOP_LATCH = auto()


@dataclass(kw_only=True)
class BasicBlock:

    label: LabelOperand
    block_type: BlockType = BlockType.NORMAL
    instructions: List[Instruction] = field(default_factory=list)

    predecessors: Set['BasicBlock'] = field(default_factory=set)
    successors: Set['BasicBlock'] = field(default_factory=set)

    dominators: Set['BasicBlock'] = field(default_factory=set)
    loop_depth: int = 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BasicBlock) and self.label.name == other.label.name

    def __hash__(self) -> int:
        return hash(self.label.name)

    def add_instruction(self, inst: Instruction) -> None:
        self.instructions.append(inst)

    def add_instruction_at_start(self, inst: Instruction) -> None:
        self.instructions.insert(0, inst)

    def terminator(self) -> Optional[Instruction]:
        if not self.instructions:
            return None
        last = self.instructions[-1]
        if isinstance(last, (JumpInst, CondJumpInst, ReturnInst)):
            return last
        return None

    def is_terminated(self) -> bool:
        return self.terminator() is not None

    def add_successor(self, block: 'BasicBlock') -> None:
        self.successors.add(block)
        block.predecessors.add(self)

    def __str__(self) -> str:
        lines = [f"{self.label}:"]
        for inst in self.instructions:
            lines.append(str(inst))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "label": self.label.to_dict(),
            "type": self.block_type.name,
            "instructions": [inst.to_dict() for inst in self.instructions],
            "predecessors": [b.label.name for b in self.predecessors],
            "successors": [b.label.name for b in self.successors],
            "loop_depth": self.loop_depth
        }


@dataclass
class ControlFlowGraph:

    name: str
    blocks: Dict[str, BasicBlock] = field(default_factory=dict)
    entry_block: Optional[BasicBlock] = None
    exit_blocks: List[BasicBlock] = field(default_factory=list)

    def create_block(self, label_name: str,
                     block_type: BlockType = BlockType.NORMAL) -> BasicBlock:
        label = LabelOperand(label_name)
        block = BasicBlock(label=label, block_type=block_type)
        self.blocks[label_name] = block

        if block_type == BlockType.ENTRY:
            self.entry_block = block

        return block

    def get_block(self, label_name: str) -> Optional[BasicBlock]:
        return self.blocks.get(label_name)

    def add_edge(self, from_label: str, to_label: str) -> bool:
        from_block = self.get_block(from_label)
        to_block = self.get_block(to_label)

        if from_block and to_block:
            from_block.add_successor(to_block)
            return True
        return False

    def get_blocks_in_order(self) -> List[BasicBlock]:
        if not self.entry_block:
            return list(self.blocks.values())

        visited = set()
        order = []

        def dfs(block: BasicBlock):
            if block.label.name in visited:
                return
            visited.add(block.label.name)
            order.append(block)
            for succ in sorted(block.successors, key=lambda b: b.label.name):
                dfs(succ)

        dfs(self.entry_block)
        for block in self.blocks.values():
            if block.label.name not in visited:
                order.append(block)

        return order

    def __str__(self) -> str:
        lines = [f"CFG for {self.name}:"]
        for block in self.get_blocks_in_order():
            lines.append(str(block))
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "entry": self.entry_block.label.name if self.entry_block else None,
            "blocks": {name: b.to_dict() for name, b in self.blocks.items()},
            "exit_blocks": [b.label.name for b in self.exit_blocks]
        }
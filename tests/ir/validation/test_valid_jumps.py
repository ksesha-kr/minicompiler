import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput
from src.ir.instructions import JumpInst, CondJumpInst


def test_valid_jumps(src_file: str) -> bool:
    with open(src_file, 'r', encoding='utf-8') as f:
        source = f.read()

    scanner = Scanner(source)
    parser = Parser(scanner.tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer(filename=src_file)
    analyzer.analyze(ast)

    generator = IRGenerator(analyzer.get_symbol_table())
    ir = generator.generate(ast)

    for func in ir.functions.values():
        all_labels = set(func.cfg.blocks.keys())

        for block in func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, JumpInst):
                    if inst.target.name not in all_labels:
                        print(f"Переход на несуществующую метку {inst.target.name}")
                        return False
                elif isinstance(inst, CondJumpInst):
                    if inst.target.name not in all_labels:
                        print(f"Условный переход на несуществующую метку {inst.target.name}")
                        return False

    print("Все переходы ведут на существующие метки")
    return True


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/ir/generation/test_if.src'
    success = test_valid_jumps(test_file)
    sys.exit(0 if success else 1)
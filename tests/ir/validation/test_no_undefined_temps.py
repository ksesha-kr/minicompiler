import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput
from src.ir.operand import TempOperand


def test_no_undefined_temps(src_file: str) -> bool:
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
        defined_temps = set()

        for block in func.cfg.get_blocks_in_order():
            for inst in block.instructions:
                if hasattr(inst, 'src1') and isinstance(inst.src1, TempOperand):
                    if inst.src1.index not in defined_temps:
                        print(f"Использование неопределённой временной {inst.src1}")
                        return False
                if hasattr(inst, 'src2') and isinstance(inst.src2, TempOperand):
                    if inst.src2.index not in defined_temps:
                        print(f"Использование неопределённой временной {inst.src2}")
                        return False

                if hasattr(inst, 'dest') and isinstance(inst.dest, TempOperand):
                    defined_temps.add(inst.dest.index)

    print("Все временные переменные определены перед использованием")
    return True


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/ir/generation/test_arithmetic.src'
    success = test_no_undefined_temps(test_file)
    sys.exit(0 if success else 1)
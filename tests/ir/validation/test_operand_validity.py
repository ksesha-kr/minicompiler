import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput
from src.ir.operand import Operand, TempOperand, VarOperand, LiteralOperand, MemoryOperand


def test_operand_validity(src_file: str) -> bool:
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
        for block in func.cfg.blocks.values():
            for inst in block.instructions:
                for attr_name in ['dest', 'src', 'src1', 'src2', 'addr', 'value', 'condition']:
                    if hasattr(inst, attr_name):
                        operand = getattr(inst, attr_name)
                        if operand is not None and not isinstance(operand, Operand):
                            print(f"Неверный операнд в {inst.type}: {operand}")
                            return False
                        if isinstance(operand, MemoryOperand):
                            if not isinstance(operand.base, (TempOperand, VarOperand)):
                                print(f"Неверный base в MemoryOperand: {operand.base}")
                                return False

    print("Все операнды корректны")
    return True


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/ir/generation/test_arithmetic.src'
    success = test_operand_validity(test_file)
    sys.exit(0 if success else 1)
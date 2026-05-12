import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput
from src.ir.basic_block import BlockType


def test_entry_block_exists(src_file: str) -> bool:
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
        if not func.cfg.entry_block:
            print(f"Функция {func.name} не имеет entry блока")
            return False

        if func.cfg.entry_block.block_type != BlockType.ENTRY:
            print(f"Entry блок функции {func.name} имеет неверный тип")
            return False

    print("Все функции имеют корректный entry блок")
    return True


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/ir/generation/test_arithmetic.src'
    success = test_entry_block_exists(test_file)
    sys.exit(0 if success else 1)
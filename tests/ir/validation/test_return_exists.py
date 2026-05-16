import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput
from src.ir.instructions import ReturnInst


def test_return_exists(src_file: str) -> bool:
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
        if func.return_type != 'void':
            has_return = False
            for block in func.cfg.blocks.values():
                for inst in block.instructions:
                    if isinstance(inst, ReturnInst):
                        has_return = True
                        break

            if not has_return:
                print(f"Функция {func.name} ({func.return_type}) не имеет RETURN")
                return False

    print("Все функции с возвращаемым значением имеют RETURN")
    return True


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/ir/generation/test_function_call.src'
    success = test_return_exists(test_file)
    sys.exit(0 if success else 1)
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput


def test_cfg_connectivity(src_file: str) -> bool:
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
            print("Отсутствует entry блок")
            return False

        visited = set()
        stack = [func.cfg.entry_block]

        while stack:
            block = stack.pop()
            if block.label.name in visited:
                continue
            visited.add(block.label.name)
            stack.extend(block.successors)

        unreachable = set(func.cfg.blocks.keys()) - visited
        if unreachable:
            print(f"Недостижимые блоки: {unreachable}")
            return False

    print("CFG связен, все блоки достижимы")
    return True


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/ir/generation/test_if.src'
    success = test_cfg_connectivity(test_file)
    sys.exit(0 if success else 1)
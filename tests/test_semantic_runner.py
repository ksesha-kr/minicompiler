import os
import sys
import glob
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer


class SemanticTestRunner:
    def __init__(self, tests_dir: str):
        self.tests_dir = Path(tests_dir)
        self.valid_dir = self.tests_dir / 'valid'
        self.invalid_dir = self.tests_dir / 'invalid'
        self.passed = 0
        self.failed = 0
        self.total = 0

    def run_all_tests(self) -> bool:
        print("ЗАПУСК ТЕСТОВ СЕМАНТИЧЕСКОГО АНАЛИЗА")

        print("\n--- ВАЛИДНЫЕ ТЕСТЫ ---")
        valid_files = sorted(glob.glob(str(self.valid_dir / '*.src')))
        for src_file in valid_files:
            expected_file = src_file.replace('.src', '.expected')
            if os.path.exists(expected_file):
                self._run_test(src_file, expected_file, expect_success=True)
            else:
                print(f"Пропущен {os.path.basename(src_file)}: нет .expected файла")

        print("\n--- НЕВАЛИДНЫЕ ТЕСТЫ ---")
        invalid_files = sorted(glob.glob(str(self.invalid_dir / '*.src')))
        for src_file in invalid_files:
            expected_file = src_file.replace('.src', '.expected')
            if os.path.exists(expected_file):
                self._run_test(src_file, expected_file, expect_success=False)
            else:
                print(f"Пропущен {os.path.basename(src_file)}: нет .expected файла")

        print(f"ИТОГИ: Пройдено: {self.passed}/{self.total} | Провалено: {self.failed}")

        return self.failed == 0

    def _run_test(self, src_file: str, expected_file: str, expect_success: bool):
        self.total += 1
        test_name = os.path.basename(src_file)
        print(f"\nТест: {test_name}")

        with open(src_file, 'r', encoding='utf-8') as f:
            source = f.read()

        scanner = Scanner(source)
        if scanner.has_errors():
            print(f"Ошибки лексера:")
            for error in scanner.errors:
                print(f"   {error}")
            self.failed += 1
            return

        parser = Parser(scanner.tokens)
        ast = parser.parse()
        if parser.errors:
            print(f"Ошибки парсера:")
            for error in parser.errors:
                print(f"   {error}")
            self.failed += 1
            return

        analyzer = SemanticAnalyzer(filename=src_file)
        analyzer.analyze(ast)

        output_lines = []

        if analyzer.get_symbol_table().scope_depth >= 0:
            output_lines.append("=== Symbol Table ===")
            output_lines.append(analyzer.get_symbol_table().dump())
            output_lines.append("")

        output_lines.append("=== Decorated AST ===")
        output_lines.append(analyzer.dump_decorated_ast(ast))
        output_lines.append("")

        if analyzer.errors.has_errors():
            output_lines.append("=== Semantic Errors ===")
            output_lines.append(str(analyzer.errors))

        actual_output = '\n'.join(output_lines).strip()

        with open(expected_file, 'r', encoding='utf-8') as f:
            expected_output = f.read().strip()

        if actual_output == expected_output:
            print("УСПЕХ")
            self.passed += 1
        else:
            print("НЕУДАЧА: Вывод не совпадает с ожидаемым")
            print("\n--- ОЖИДАЛОСЬ ---")
            print(expected_output[:800] + ("..." if len(expected_output) > 800 else ""))
            print("\n--- ПОЛУЧЕНО ---")
            print(actual_output[:800] + ("..." if len(actual_output) > 800 else ""))

            self._show_diff(expected_output, actual_output)
            self.failed += 1

    def _show_diff(self, expected: str, actual: str):
        expected_lines = expected.split('\n')
        actual_lines = actual.split('\n')

        for i, (exp, act) in enumerate(zip(expected_lines, actual_lines)):
            if exp != act:
                print(f"\nРазличие в строке {i + 1}:")
                print(f"   Ожидалось: '{exp}'")
                print(f"   Получено:  '{act}'")
                break
        else:
            if len(expected_lines) != len(actual_lines):
                print(f"\nРазличие в количестве строк:")
                print(f"   Ожидалось: {len(expected_lines)} строк")
                print(f"   Получено:  {len(actual_lines)} строк")


def main():
    tests_dir = Path(__file__).parent / 'semantic'
    runner = SemanticTestRunner(str(tests_dir))
    success = runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
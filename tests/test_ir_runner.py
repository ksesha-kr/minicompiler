import os
import sys
import glob
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.output import IROutput


class IRTestRunner:

    def __init__(self, tests_dir: str):
        self.tests_dir = Path(tests_dir)
        self.generation_dir = self.tests_dir / 'generation'
        self.validation_dir = self.tests_dir / 'validation'
        self.passed = 0
        self.failed = 0
        self.total = 0

    def run_all_tests(self) -> bool:
        print("ЗАПУСК ТЕСТОВ IR GENERATION")

        print("\n--- GENERATION TESTS ---")
        if self.generation_dir.exists():
            for src_file in sorted(glob.glob(str(self.generation_dir / '*.src'))):
                expected_file = src_file.replace('.src', '.expected')
                if os.path.exists(expected_file):
                    self._run_generation_test(src_file, expected_file)
                else:
                    print(f"{os.path.basename(src_file)}: нет .expected")
        else:
            print("Директория generation/ не найдена")

        print("\n--- VALIDATION TESTS ---")
        if self.validation_dir.exists():
            for py_file in sorted(glob.glob(str(self.validation_dir / 'test_*.py'))):
                self._run_validation_test(py_file)
        else:
            print("Директория validation/ не найдена")

        print(f"ИТОГИ: Пройдено: {self.passed}/{self.total} | Провалено: {self.failed}")

        return self.failed == 0

    def _run_generation_test(self, src_file: str, expected_file: str):
        self.total += 1
        test_name = os.path.basename(src_file)
        print(f"\n{test_name}")

        try:
            with open(src_file, 'r', encoding='utf-8') as f:
                source = f.read()

            scanner = Scanner(source)
            if scanner.has_errors():
                print(f"Ошибки лексера")
                self.failed += 1
                return

            parser = Parser(scanner.tokens)
            ast = parser.parse()
            if parser.errors:
                print(f"Ошибки парсера")
                self.failed += 1
                return

            analyzer = SemanticAnalyzer(filename=src_file)
            if not analyzer.analyze(ast):
                print(f"Семантические ошибки")
                self.failed += 1
                return

            generator = IRGenerator(analyzer.get_symbol_table())
            ir = generator.generate(ast)

            actual = IROutput.to_text(ir).strip()

            with open(expected_file, 'r', encoding='utf-8') as f:
                expected = f.read().strip()

            if actual == expected:
                print("УСПЕХ")
                self.passed += 1
            else:
                print("НЕУДАЧА: Вывод не совпадает")
                print("ОЖИДАЛОСЬ:")
                print(expected)
                print("\nПОЛУЧЕНО:")
                print(actual)
                self.failed += 1

        except Exception as e:
            print(f"Ошибка: {e}")
            self.failed += 1

    def _run_validation_test(self, py_file: str):
        self.total += 1
        test_name = os.path.basename(py_file)
        print(f"\n{test_name}")

        try:
            result = subprocess.run(
                [sys.executable, py_file],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '+' in line:
                        print(f"+ {line.strip()}")
                        break
                self.passed += 1
            else:
                print(f"{result.stdout.strip()}")
                if result.stderr:
                    print(f"   {result.stderr.strip()}")
                self.failed += 1

        except subprocess.TimeoutExpired:
            print("Таймаут")
            self.failed += 1
        except Exception as e:
            print(f"Ошибка: {e}")
            self.failed += 1

    def _show_diff(self, expected: str, actual: str):
        exp_lines = expected.split('\n')
        act_lines = actual.split('\n')

        for i, (e, a) in enumerate(zip(exp_lines, act_lines)):
            if e != a:
                print(f"   Строка {i + 1}:")
                print(f"     Expected: {e}")
                print(f"     Actual:   {a}")
                break


def main():
    tests_dir = Path(__file__).parent / 'ir'
    runner = IRTestRunner(str(tests_dir))
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
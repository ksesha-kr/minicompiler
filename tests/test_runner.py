import os
import sys
import glob
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer.scanner import Scanner


class TestRunner:

    def __init__(self, tests_dir: str):
        self.tests_dir = Path(tests_dir)
        self.valid_dir = self.tests_dir / 'valid'
        self.invalid_dir = self.tests_dir / 'invalid'

        self.passed = 0
        self.failed = 0
        self.total = 0

    def run_all_tests(self) -> bool:
        print("ЗАПУСК ТЕСТОВ ЛЕКСИЧЕСКОГО АНАЛИЗАТОРА")

        print("\n--- ВАЛИДНЫЕ ТЕСТЫ ---")
        valid_tests = sorted(glob.glob(str(self.valid_dir / '*.src')))
        for test_file in valid_tests:
            expected_file = test_file.replace('.src', '.expected')
            if os.path.exists(expected_file):
                self._run_test(test_file, expected_file, expect_success=True)
            else:
                print(f"Пропущен {test_file}: нет файла ожидаемого вывода")

        print("\n--- НЕВАЛИДНЫЕ ТЕСТЫ ---")
        invalid_test = self.invalid_dir / 'test_errors.src'
        expected_file = self.invalid_dir / 'test_errors.expected'

        if invalid_test.exists() and expected_file.exists():
            self._run_test(str(invalid_test), str(expected_file), expect_success=False)
        else:
            print(f"Пропущен: нет файла test_errors.src или test_errors.expected")

        print(f"ИТОГИ: Пройдено: {self.passed}/{self.total} | "
              f"Провалено: {self.failed}")

        return self.failed == 0

    def _run_test(self, test_file: str, expected_file: str, expect_success: bool):
        self.total += 1
        test_name = os.path.basename(test_file)

        print(f"\nТест: {test_name}")

        with open(test_file, 'r', encoding='utf-8') as f:
            source = f.read()

        scanner = Scanner(source)
        tokens = scanner.tokens

        output_lines = []
        for token in tokens:
            output_lines.append(str(token))

        actual_output = '\n'.join(output_lines)

        with open(expected_file, 'r', encoding='utf-8') as f:
            expected_output = f.read().strip()

        if actual_output.strip() == expected_output.strip():
            print(f"УСПЕХ")
            self.passed += 1
        else:
            print(f"НЕУДАЧА: Вывод не совпадает с ожидаемым")
            print("\n--- ОЖИДАЛОСЬ ---")
            print(expected_output)
            print("--- ПОЛУЧЕНО ---")
            print(actual_output)

            self._show_diff(expected_output, actual_output)
            self.failed += 1

    def _show_diff(self, expected: str, actual: str):
        expected_lines = expected.split('\n')
        actual_lines = actual.split('\n')

        for i, (exp, act) in enumerate(zip(expected_lines, actual_lines)):
            if exp != act:
                print(f"\nРазличие в строке {i + 1}:")
                print(f"  Ожидалось: '{exp}'")
                print(f"  Получено:  '{act}'")
                break


def create_expected_files():
    tests_dir = Path(__file__).parent / 'lexer'

    for src_file in glob.glob(str(tests_dir / 'valid' / '*.src')):
        expected_file = src_file.replace('.src', '.expected')

        with open(src_file, 'r', encoding='utf-8') as f:
            source = f.read()

        scanner = Scanner(source)

        with open(expected_file, 'w', encoding='utf-8') as f:
            for token in scanner.tokens:
                f.write(str(token) + '\n')

        print(f"Создан: {expected_file}")

    invalid_src = tests_dir / 'invalid' / 'test_errors.src'
    if invalid_src.exists():
        expected_file = tests_dir / 'invalid' / 'test_errors.expected'

        with open(invalid_src, 'r', encoding='utf-8') as f:
            source = f.read()

        scanner = Scanner(source)

        with open(expected_file, 'w', encoding='utf-8') as f:
            for token in scanner.tokens:
                f.write(str(token) + '\n')

        print(f"Создан: {expected_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--create-expected':
        create_expected_files()
        return

    tests_dir = os.path.join(os.path.dirname(__file__), 'lexer')
    runner = TestRunner(tests_dir)
    success = runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

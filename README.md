# MiniCompiler

Проект компилятора для упрощённого C-подобного языка.

## Описание проекта

MiniCompiler - это учебный проект компилятора, реализуемый поэтапно.

### Возможности лексера

- **Ключевые слова**: `if`, `else`, `while`, `for`, `int`, `float`, `bool`, `return`, `true`, `false`, `void`, `struct`, `fn`
- **Идентификаторы**: буквы, цифры, _, до 255 символов
- **Литералы**: целые, вещественные, строковые, булевы
- **Операторы**: арифметические (`+ - * / %`), сравнения (`== != < <= > >=`), логические (`&& || !`), присваивание (`=`)
- **Разделители**: `( ) { } [ ] ; , .`
- **Комментарии**: однострочные `//` и многострочные `/* */` с поддержкой вложенности
- **Отслеживание позиции**: номер строки и колонки для каждого токена
- **Обработка ошибок**: обнаружение и восстановление после ошибок с понятными сообщениями

## Требования

- Python 3.8 или выше
- (Опционально) virtualenv для изоляции окружения

## Установка

### 1. Клонирование репозитория

```bash
git clone <url-репозитория>
cd minicompiler
```

### 2. Создание виртуального окружения (рекомендуется)

```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac

venv\Scripts\activate     # для Windows
```

### 3. Установка пакета

```bash
pip install -e .
```

### Запуск лексера на примере

```bash
minicompiler-lex examples/hello.src

minicompiler-lex examples/hello.src -o output.txt

python -m src.lexer.scanner examples/hello.src
```

## Запуск тестов

```bash
python tests/test_runner.py
```

### Ожидаемая структура тестов

Проект включает следующие тесты:

**Валидные тесты** (`tests/lexer/valid/`):
- `test_identifiers.src` - проверка идентификаторов
- `test_keywords.src` - проверка ключевых слов
- `test_numbers.src` - проверка числовых литералов
- `test_operators.src` - проверка операторов
- `test_comments.src` - проверка комментариев

**Невалидные тесты** (`tests/lexer/invalid/`):
- `test_invalid_char.src` - недопустимые символы
- `test_malformed_number.src` - некорректные числа
- `test_unterminated_string.src` - незавершённые строки

## Формат вывода токенов

Каждый токен выводится в формате:

```
СТРОКА:КОЛОНКА ТИП_ТОКЕНА "ЛЕКСЕМА" [ЗНАЧЕНИЕ]
```

Где:
- `СТРОКА` - номер строки (начиная с 1)
- `КОЛОНКА` - номер колонки (начиная с 1)
- `ТИП_ТОКЕНА` - тип токена из перечисления TokenType
- `ЛЕКСЕМА` - исходный текст, соответствующий токену
- `ЗНАЧЕНИЕ` - литеральное значение (для чисел, строк, ошибок)

Примеры:
```
1:1 KW_IF "if"
1:4 IDENTIFIER "x"
2:1 INT_LITERAL "42" 42
3:1 ERROR "@" Недопустимый символ '@'
```

## Команды проекта

| Команда | Описание |
|---------|----------|
| `pip install -e .` | Установка в режиме разработки |
| `minicompiler-lex file.src` | Запуск лексера на файле |
| `minicompiler-lex file.src -o out.txt` | Запуск с сохранением в файл |
| `python -m src.lexer.scanner file.src` | Запуск через модуль |
| `python tests/test_runner.py` | Запуск всех тестов |
| `python tests/test_runner.py --create-expected` | Создание эталонных файлов |

## Синтаксический анализ

Парсер преобразует поток токенов в абстрактное синтаксическое дерево (AST).

### Запуск парсера

```bash
# Текстовый вывод AST
python -m src.main parse --input program.src --ast-format text

# JSON вывод
python -m src.main parse --input program.src --ast-format json

# Graphviz DOT формат
python -m src.main parse --input program.src --ast-format dot --output ast.dot
dot -Tpng ast.dot -o ast.png  # конвертация в изображение
```
## Семантический анализ

Проверка типов, областей видимости и правил языка.

### Запуск

```bash
# Базовая проверка
python -m src.main check --input program.src

# Показать таблицу символов
python -m src.main check --input program.src --show-symbols

# Показать AST с типовыми аннотациями
python -m src.main check --input program.src --show-types

# Сохранить вывод в файл
python -m src.main check --input program.src --output result.txt

```

### Опции парсера

| Опция | Описание |
|-------|----------|
| `--input, -i` | Входной файл |
| `--output, -o` | Файл вывода |
| `--ast-format, -f` | Формат: `text`, `json`, `dot` |
| `--verbose, -v` | Подробный вывод |

### Пример вывода (text)

```
Program [line 1]:
  FunctionDecl: main -> void [line 1]:
    Body:
      Block [line 1]:
        ExprStmt [line 2]:
          Assignment: = [line 2]
            Target: Identifier: x
            Value: Literal: 42 (int)
```

### Запуск тестов парсера

```bash
python tests/test_parser_runner.py
```
### Запуск тестов семантики
```
python tests/test_semantic_runner.py
```

## Грамматика языка

### Краткая справка

```ebnf
Program      ::= { Declaration }
Declaration  ::= FunctionDecl | StructDecl | VarDecl
Expression   ::= Assignment (с учётом приоритета операторов)
```

Приоритет операторов (высший → низший):
1. Унарные: `-` `!`
2. Мультипликативные: `*` `/` `%`
3. Аддитивные: `+` `-`
4. Отношения: `<` `<=` `>` `>=`
5. Равенство: `==` `!=`
6. Логические: `&&` `\|\|`
7. Присваивание: `=`

## Структура проекта

```
minicompiler/
├── src/
│   ├── lexer/             
│   │   ├── scanner.py
│   │   └── token.py
│   ├── parser/            
│   │   ├── parser.py
│   │   ├── ast.py
│   │   ├── __init__.py
│   │   └── grammar.txt
│   └── main.py
├── tests/
│   ├── test_runner.py          
│   ├── test_parser_runner.py    
│   ├── lexer/
│   └── parser/                 
│       ├── valid/
│       └── invalid/
├── docs/
│   └── grammar.md 
│   └── language_spec.md
├── examples/
├── README.md
└── pyproject.toml
```

## Быстрый старт

```bash
# 1. Лексический анализ
python -m src.main lex --input examples/hello.src

# 2. Синтаксический анализ
python -m src.main parse --input examples/hello.src --ast-format text

# 3. Запуск всех тестов
python tests/test_runner.py          # лексер
python tests/test_parser_runner.py   # парсер
```

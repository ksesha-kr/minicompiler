# Грамматика языка MiniCompiler

## 1. Нотация и термины

### 1.1. Обозначения EBNF (ISO/IEC 14977)

| Символ | Значение | Пример |
|--------|----------|--------|
| `::=` | Определение | `Expr ::= Term` |
| `|` | Альтернатива | `A \| B` — A или B |
| `[ ... ]` | Необязательный элемент | `[ "+" Term ]` |
| `{ ... }` | Повторение (0 или более) | `{ "," Expr }` |
| `( ... )` | Группировка | `( "+" \| "-" ) Term` |
| `"..."` | Терминал (литерал) | `"if"`, `"+"` |
| *Идентификатор* | Нетерминал | `Expression`, `Statement` |

### 1.2. Термины

- **Терминал** — лексема, возвращаемая лексером (токен)
- **Нетерминал** — синтаксическая категория, определяемая правилами грамматики
- **Начальный символ** — `Program`, корень дерева вывода
- **LL(1)** — грамматика, допускающая нисходящий разбор с одним токеном lookahead

## 2. Лексическая основа (терминалы)

Терминалы соответствуют типам токенов из лексера (`src/lexer/token.py`).

### 2.1. Ключевые слова (зарезервированные идентификаторы)

```
"fn" | "struct" | "if" | "else" | "while" | "for" | "return" |
"int" | "float" | "bool" | "void" | "true" | "false"
```

### 2.2. Литералы

```ebnf
IntegerLiteral  ::= digit { digit }
FloatLiteral    ::= digit { digit } "." { digit } | digit "." { digit }
StringLiteral   ::= '"' { Character } '"'
BooleanLiteral  ::= "true" | "false"
digit           ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
Character       ::= любой печатный символ, кроме '"' и '\'
```

### 2.3. Идентификаторы

```ebnf
Identifier ::= Letter { Letter | Digit | "_" }
Letter     ::= "a"…"z" | "A"…"Z" | "_"
Digit      ::= "0"…"9"
```

Максимальная длина — 255 символов

### 2.4. Операторы и разделители

```
Арифметические:  "+" | "-" | "*" | "/" | "%"
Сравнения:       "==" | "!=" | "<" | "<=" | ">" | ">="
Логические:      "&&" | "||" | "!"
Присваивание:    "="
Разделители:     "(" | ")" | "{" | "}" | "[" | "]" | ";" | "," | "." | "->"
```

### 2.5. Комментарии (обрабатываются лексером, исключаются из потока токенов)

```ebnf
LineComment   ::= "//" { Character } "\n"
BlockComment  ::= "/*" { any } "*/"
```

## 3. Контекстно-свободная грамматика (формальная спецификация)

### 3.1. Корень программы

```ebnf
Program ::= { Declaration }
```

### 3.2. Объявления верхнего уровня

```ebnf
Declaration ::= FunctionDeclaration | StructDeclaration | TopLevelVarDeclaration

FunctionDeclaration ::= "fn" Identifier "(" [ ParameterList ] ")" [ "->" Type ] Block

StructDeclaration ::= "struct" Identifier "{" { VarDeclaration } "}"

TopLevelVarDeclaration ::= Type Identifier [ "=" Expression ] ";"

ParameterList ::= Parameter { "," Parameter }
Parameter     ::= Type Identifier

Type ::= "int" | "float" | "bool" | "void" | Identifier
```

### 3.3. Операторы (внутри функций/блоков)

```ebnf
Statement ::= 
      Block
    | IfStatement
    | WhileStatement
    | ForStatement
    | ReturnStatement
    | ExpressionStatement
    | VarDeclaration

Block ::= "{" { Statement } "}"

IfStatement ::= "if" "(" Expression ")" Statement [ "else" Statement ]

WhileStatement ::= "while" "(" Expression ")" Statement

ForStatement ::= "for" "(" [ ExpressionStatement ] ";" 
                       [ Expression ] ";" 
                       [ Expression ] ")" Statement

ReturnStatement ::= "return" [ Expression ] ";"

ExpressionStatement ::= Expression ";"
```

### 3.4. Выражения (с учётом приоритета операторов)

Грамматика построена по уровням приоритета (от низшего к высшему), что обеспечивает корректный разбор без скобок.

```ebnf
Expression      ::= Assignment

Assignment      ::= LogicalOr [ "=" LogicalOr ]

LogicalOr       ::= LogicalAnd { "||" LogicalAnd }

LogicalAnd      ::= Equality { "&&" Equality }

Equality        ::= Relational { ( "==" | "!=" ) Relational }

Relational      ::= Additive { ( "<" | "<=" | ">" | ">=" ) Additive }

Additive        ::= Multiplicative { ( "+" | "-" ) Multiplicative }

Multiplicative  ::= Unary { ( "*" | "/" | "%" ) Unary }

Unary           ::= [ "-" | "!" ] Primary

Primary         ::= Literal
                 | Identifier
                 | Identifier "(" [ ArgumentList ] ")"
                 | "(" Expression ")"

ArgumentList    ::= Expression { "," Expression }

Literal         ::= IntegerLiteral | FloatLiteral | StringLiteral | BooleanLiteral
```

### 3.5. Таблица соответствия правил и методов парсера

| Правило грамматики | Метод в `parser.py` |
|-------------------|---------------------|
| `Program` | `_parse_program()` |
| `Declaration` | `_parse_declaration()` |
| `FunctionDeclaration` | `_parse_function_decl()` |
| `StructDeclaration` | `_parse_struct_decl()` |
| `VarDeclaration` | `_parse_var_decl()` |
| `Statement` | `_parse_statement()` |
| `Block` | `_parse_block()` |
| `IfStatement` | `_parse_if_stmt()` |
| `WhileStatement` | `_parse_while_stmt()` |
| `ForStatement` | `_parse_for_stmt()` |
| `ReturnStatement` | `_parse_return_stmt()` |
| `Expression` | `_parse_expression()` |
| `Assignment` | `_parse_assignment()` |
| `LogicalOr` | `_parse_logical_or()` |
| `LogicalAnd` | `_parse_logical_and()` |
| `Equality` | `_parse_equality()` |
| `Relational` | `_parse_relational()` |
| `Additive` | `_parse_additive()` |
| `Multiplicative` | `_parse_multiplicative()` |
| `Unary` | `_parse_unary()` |
| `Primary` | `_parse_primary()` |

## 4. Приоритет и ассоциативность операторов

### 4.1. Таблица приоритета (от высшего к низшему)

| Уровень | Операторы | Тип | Ассоциативность |
|---------|-----------|-----|-----------------|
| 1 | `-` `!` | Унарные | Право-ассоциативные |
| 2 | `*` `/` `%` | Мультипликативные | Лево-ассоциативные |
| 3 | `+` `-` | Аддитивные | Лево-ассоциативные |
| 4 | `<` `<=` `>` `>=` | Отношения | Неассоциативные |
| 5 | `==` `!=` | Равенство | Неассоциативные |
| 6 | `&&` | Логическое И | Лево-ассоциативные |
| 7 | `\|\|` | Логическое ИЛИ | Лево-ассоциативные |
| 8 | `=` | Присваивание | Право-ассоциативные |

### 4.2. Примеры разбора

```
// Пример 1: приоритет * над +
a + b * c
→ Additive(Identifier(a), "+", Multiplicative(Identifier(b), "*", Identifier(c)))

// Пример 2: лево-ассоциативность +
a + b + c
→ Additive(Additive(a, "+", b), "+", c)

// Пример 3: право-ассоциативность =
a = b = c
→ Assignment(a, "=", Assignment(b, "=", c))

// Пример 4: унарные операторы
-!x
→ Unary("-", Unary("!", Identifier(x)))
```

## 5. Свойства грамматики

### 5.1. LL(1)-совместимость

Грамматика спроектирована как LL(1) для поддержки рекурсивного спуска:

| Нетерминал | FIRST-множество | FOLLOW-множество | Конфликтов |
|------------|-----------------|------------------|------------|
| `Declaration` | {`"fn"`, `"struct"`, `"int"`, `"float"`, `"bool"`, `Identifier`} | {`$`, `"fn"`, `"struct"`, ...} | Нет |
| `Statement` | {`"{"`, `"if"`, `"while"`, `"for"`, `"return"`, `Identifier`, `"int"`, ...} | {`"}"`, `";"`, `"else"`, `$`} | Нет |
| `Primary` | {`Literal`, `Identifier`, `"("`} | {операторы, `")"`, `";"`, `","`} | Нет |

### 5.2. Обработка неоднозначностей

| Неоднозначность | Решение |
|-----------------|---------|
| Dangling else | `else` связывается с ближайшим `if` (реализовано в `_parse_if_stmt()`) |
| Присваивание в выражении | Только `=` на уровне `Assignment`, не вложен в другие выражения |
| Вызов функции vs. скобки в выражении | `Identifier "("` распознаётся как `Call` в `_parse_primary()` |

## 6. Примеры вывода дерева разбора

### 6.1. Программа

**Исходный код:**
```c
fn main() -> void {
    x = 1 + 2 * 3;
}
```

**Дерево вывода (упрощённо):**
```
Program
└─ FunctionDeclaration("main", -> void)
   └─ Block
      └─ ExpressionStatement
         └─ Assignment("x", =, Expression)
            └─ Additive("+")
               ├─ Identifier("x")
               └─ Multiplicative("*")
                  ├─ Literal(1)
                  └─ Literal(2)
               └─ Literal(3)  // * имеет приоритет над +
```

### 6.2. Условный оператор

**Исходный код:**
```c
if (a > 0) {
    b = 1;
} else {
    b = 0;
}
```

**Дерево вывода:**
```
IfStatement
├─ Condition: Relational(">", Identifier(a), Literal(0))
├─ Then: Block
│  └─ Assignment("b", =, Literal(1))
└─ Else: Block
   └─ Assignment("b", =, Literal(0))
```


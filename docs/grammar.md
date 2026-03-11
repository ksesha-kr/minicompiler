# Грамматика языка MiniCompiler

Этот документ содержит формальную спецификацию грамматики языка MiniCompiler

## Обзор

### Ключевые особенности

| Характеристика | Значение |
|----------------|----------|
| Типизация | Статическая |
| Синтаксис | C-подобный |
| Парсинг | Рекурсивный спуск (LL(1)) |
| Кодировка | UTF-8 |

## Лексические элементы

### Ключевые слова

```
fn          struct      if          else
while       for         return      int
float       bool        void        true
false
```

### Типы данных

| Тип | Описание | Размер |
|-----|----------|--------|
| `int` | Целое число со знаком | 32 бита |
| `float` | Число с плавающей точкой | 64 бита |
| `bool` | Логический тип | 1 бит |
| `void` | Отсутствие типа | - |

### Операторы

| Категория | Операторы |
|-----------|-----------|
| Арифметические | `+` `-` `*` `/` `%` |
| Сравнения | `<` `<=` `>` `>=` `==` `!=` |
| Логические | `&&` `\|\|` `!` |
| Присваивания | `=` |
| Другие | `(` `)` `{` `}` `[` `]` `;` `,` `.` `->` |

### Литералы

```ebnf
Integer     ::= digit { digit }
Float       ::= digit { digit } "." { digit }
String      ::= '"' { character } '"'
Boolean     ::= "true" | "false"
digit       ::= [0-9]
character   ::= любой печатный символ кроме " и \
```

### Идентификаторы

```ebnf
Identifier  ::= letter { letter | digit | "_" }
letter      ::= [a-zA-Z]
```

**Правила:**
- Начинается с буквы или `_`
- Может содержать буквы, цифры и `_`
- Регистрозависимый
- Максимальная длина: 255 символов

### Комментарии

```ebnf
LineComment     ::= "//" { любой символ кроме \n }
BlockComment    ::= "/*" { любой символ } "*/"
```

## Формальная грамматика

### Программа

```ebnf
Program         ::= { Declaration }
```

### Объявления

```ebnf
Declaration     ::= FunctionDecl | StructDecl | VarDecl

FunctionDecl    ::= "fn" Identifier "(" [ Parameters ] ")" [ "->" Type ] Block

StructDecl      ::= "struct" Identifier "{" { VarDecl } "}"

VarDecl         ::= Type Identifier [ "=" Expression ] ";"

Parameters      ::= Parameter { "," Parameter }

Parameter       ::= Type Identifier

Type            ::= "int" | "float" | "bool" | "void" | Identifier
```

### Операторы

```ebnf
Statement       ::= Block | IfStmt | WhileStmt | ForStmt | ReturnStmt | ExprStmt | VarDecl

Block           ::= "{" { Statement } "}"

IfStmt          ::= "if" "(" Expression ")" Statement [ "else" Statement ]

WhileStmt       ::= "while" "(" Expression ")" Statement

ForStmt         ::= "for" "(" [ ExprStmt ] ";" [ Expression ] ";" [ Expression ] ")" Statement

ReturnStmt      ::= "return" [ Expression ] ";"

ExprStmt        ::= Expression ";"
```

### Выражения

```ebnf
Expression      ::= Assignment

Assignment      ::= LogicalOr [ "=" Assignment ]

LogicalOr       ::= LogicalAnd { "||" LogicalAnd }

LogicalAnd      ::= Equality { "&&" Equality }

Equality        ::= Relational { ( "==" | "!=" ) Relational }

Relational      ::= Additive { ( "<" | "<=" | ">" | ">=" ) Additive }

Additive        ::= Multiplicative { ( "+" | "-" ) Multiplicative }

Multiplicative  ::= Unary { ( "*" | "/" | "%" ) Unary }

Unary           ::= [ "-" | "!" ] Primary

Primary         ::= Literal | Identifier | "(" Expression ")" | Call

Call            ::= Identifier "(" [ Arguments ] ")"

Arguments       ::= Expression { "," Expression }

Literal         ::= Integer | Float | String | Boolean
```

## Приоритет операторов

Операторы перечислены от **высшего** приоритета к **низшему**:

| Уровень | Операторы | Описание |
|---------|-----------|----------|
| 1 | `-` `!` | Унарные (отрицание, логическое НЕ) |
| 2 | `*` `/` `%` | Мультипликативные |
| 3 | `+` `-` | Аддитивные |
| 4 | `<` `<=` `>` `>=` | Отношения |
| 5 | `==` `!=` | Равенство |
| 6 | `&&` | Логическое И |
| 7 | `\|\|` | Логическое ИЛИ |
| 8 | `=` | Присваивание |

## Ассоциативность

| Ассоциативность | Операторы |
|-----------------|-----------|
| **Слева направо** | `+` `-` `*` `/` `%` `&&` `\|\|` `==` `!=` `<` `<=` `>` `>=` |
| **Справа налево** | `=` |
| **Не ассоциативны** | `-` `!` (унарные) |

### Примеры ассоциативности

```
// Слева направо:
a + b + c     ≡  (a + b) + c
a * b / c     ≡  (a * b) / c
a && b && c   ≡  (a && b) && c

// Справа налево:
a = b = c     ≡  a = (b = c)

// Приоритет:
a + b * c     ≡  a + (b * c)
a && b || c   ≡  (a && b) || c
```

## Примеры

### Простая программа

```c
fn main() -> void {
    x = 5;
    y = x + 10;
}
```

### Функция с параметрами

```c
fn add(a: int, b: int) -> int {
    return a + b;
}

fn main() -> void {
    result = add(1, 2);
}
```

### Условный оператор

```c
fn main() -> void {
    if (x > 0) {
        y = 1;
    } else {
        y = 0;
    }
}
```

### Цикл while

```c
fn factorial(n: int) -> int {
    result = 1;
    while (n > 0) {
        result = result * n;
        n = n - 1;
    }
    return result;
}
```

### Цикл for

```c
fn main() -> void {
    for (i = 0; i < 10; i = i + 1) {
        print(i);
    }
}
```

### Структура

```c
struct Point {
    int x;
    int y;
}

fn main() -> void {
    p.x = 10;
    p.y = 20;
}
```

### Сложное выражение

```c
fn main() -> void {
    result = (a + b) * (c - d) / 2;
    check = x > 0 && y < 10 || z == 5;
}
```

## Обработка ошибок

### Синтаксические ошибки

| Ошибка | Сообщение |
|--------|-----------|
| Пропущена `)` | `Ожидается ')' после выражения` |
| Пропущена `;` | `Ожидается ';' после выражения` |
| Пропущена `}` | `Ожидается '}' после блока` |
| Неверный тип | `Ожидается тип` |

### Восстановление после ошибок

Парсер использует **panic mode recovery**:
1. При ошибке пропускает токены
2. Останавливается на точке синхронизации (`;`, `}`, `fn`, `struct`, etc.)
3. Продолжает парсинг следующего объявления

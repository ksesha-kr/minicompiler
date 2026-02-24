from typing import List
from .token import Token, TokenType


class Scanner:
    keywords = {
        'if': TokenType.KW_IF,
        'else': TokenType.KW_ELSE,
        'while': TokenType.KW_WHILE,
        'for': TokenType.KW_FOR,
        'int': TokenType.KW_INT,
        'float': TokenType.KW_FLOAT,
        'bool': TokenType.KW_BOOL,
        'return': TokenType.KW_RETURN,
        'true': TokenType.KW_TRUE,
        'false': TokenType.KW_FALSE,
        'void': TokenType.KW_VOID,
        'struct': TokenType.KW_STRUCT,
        'fn': TokenType.KW_FN
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.errors = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.scan_tokens()

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.END_OF_FILE, "", self.line + 1, 1))

    def scan_token(self):
        c = self.advance()

        if c == ' ' or c == '\r' or c == '\t':
            pass
        elif c == '\n':
            self.line += 1
            self.column = 1
            return

        elif c == '/':
            if self.match('/'):
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            elif self.match('*'):
                self.multiline_comment()
            else:
                self.add_token(TokenType.OP_DIV)

        elif c == '+':
            self.add_token(TokenType.OP_PLUS)
        elif c == '-':
            if self.peek().isdigit():
                self.scan_number()
            else:
                self.add_token(TokenType.OP_MINUS)
        elif c == '*':
            self.add_token(TokenType.OP_MUL)
        elif c == '%':
            self.add_token(TokenType.OP_MOD)
        elif c == '(':
            self.add_token(TokenType.LPAREN)
        elif c == ')':
            self.add_token(TokenType.RPAREN)
        elif c == '{':
            self.add_token(TokenType.LBRACE)
        elif c == '}':
            self.add_token(TokenType.RBRACE)
        elif c == '[':
            self.add_token(TokenType.LBRACKET)
        elif c == ']':
            self.add_token(TokenType.RBRACKET)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == '.':
            self.add_token(TokenType.DOT)

        elif c == '=':
            if self.match('='):
                self.add_token(TokenType.OP_EQ)
            else:
                self.add_token(TokenType.OP_ASSIGN)
        elif c == '!':
            if self.match('='):
                self.add_token(TokenType.OP_NE)
            else:
                self.add_token(TokenType.OP_NOT)
        elif c == '<':
            if self.match('='):
                self.add_token(TokenType.OP_LE)
            else:
                self.add_token(TokenType.OP_LT)
        elif c == '>':
            if self.match('='):
                self.add_token(TokenType.OP_GE)
            else:
                self.add_token(TokenType.OP_GT)
        elif c == '&':
            if self.match('&'):
                self.add_token(TokenType.OP_AND)
            else:
                self.error(f"Недопустимый символ '&'")
        elif c == '|':
            if self.match('|'):
                self.add_token(TokenType.OP_OR)
            else:
                self.error(f"Недопустимый символ '|'")

        elif c == '"':
            self.scan_string()

        elif c.isdigit():
            self.scan_number()

        elif c.isalpha() or c == '_':
            self.scan_identifier()

        else:
            self.error(f"Недопустимый символ '{c}'")

    def scan_identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()

        text = self.source[self.start:self.current]

        if len(text) > 255:
            self.error("Слишком длинный идентификатор")
            return

        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type)

    def scan_number(self):
        start_line = self.line
        start_col = self.column - 1

        number_start = self.current - 1

        while self.peek().isdigit():
            self.advance()

        dot_count = 0

        while True:
            if self.peek() == '.':
                dot_count += 1
                self.advance()

                if not self.peek().isdigit():
                    text = self.source[number_start:self.current]
                    self.errors.append(f"Ошибка на {start_line}:{start_col}: Некорректное число")
                    self.tokens.append(Token(TokenType.ERROR, text, start_line, start_col,
                                             f"Некорректное число: '{text}'"))
                    return

                while self.peek().isdigit():
                    self.advance()
            else:
                break

        text = self.source[number_start:self.current]

        if dot_count > 1:
            self.errors.append(f"Ошибка на {start_line}:{start_col}: Некорректное число")
            self.tokens.append(Token(TokenType.ERROR, text, start_line, start_col,
                                     f"Некорректное число: '{text}'"))
            return

        if self.peek().isalpha():
            try:
                if '.' in text:
                    value = float(text)
                    self.tokens.append(Token(TokenType.FLOAT_LITERAL, text, start_line, start_col, value))
                else:
                    value = int(text)
                    if value < -2 ** 31 or value > 2 ** 31 - 1:
                        self.errors.append(f"Ошибка на {start_line}:{start_col}: Число вне диапазона")
                        self.tokens.append(Token(TokenType.ERROR, text, start_line, start_col,
                                                 f"Целочисленный литерал {value} вне допустимого диапазона [-2³¹, 2³¹-1]"))
                    else:
                        self.tokens.append(Token(TokenType.INT_LITERAL, text, start_line, start_col, value))
            except ValueError:
                self.errors.append(f"Ошибка на {start_line}:{start_col}: Некорректное число")
                self.tokens.append(Token(TokenType.ERROR, text, start_line, start_col,
                                         f"Некорректное число: '{text}'"))
            return

        try:
            if '.' in text:
                value = float(text)
                self.tokens.append(Token(TokenType.FLOAT_LITERAL, text, start_line, start_col, value))
            else:
                value = int(text)
                if value < -2 ** 31 or value > 2 ** 31 - 1:
                    self.errors.append(f"Ошибка на {start_line}:{start_col}: Число вне диапазона")
                    self.tokens.append(Token(TokenType.ERROR, text, start_line, start_col,
                                             f"Целочисленный литерал {value} вне допустимого диапазона [-2³¹, 2³¹-1]"))
                else:
                    self.tokens.append(Token(TokenType.INT_LITERAL, text, start_line, start_col, value))
        except ValueError:
            self.errors.append(f"Ошибка на {start_line}:{start_col}: Некорректное число")
            self.tokens.append(Token(TokenType.ERROR, text, start_line, start_col,
                                     f"Некорректное число: '{text}'"))

    def scan_string(self):
        start_line = self.line
        start_col = self.column - 1

        open_quote_pos = self.start

        while not self.is_at_end() and self.peek() != '"' and self.peek() != '\n':
            self.advance()

        if self.is_at_end() or self.peek() == '\n':
            text = self.source[open_quote_pos:self.current]
            display_text = text + '"' if not text.endswith('"') else text
            self.errors.append(f"Ошибка на {start_line}:{start_col}: Незавершённая строка")
            self.tokens.append(Token(TokenType.ERROR, display_text, start_line, start_col,
                                     "Незавершённая строка"))
            return

        self.advance()
        text = self.source[open_quote_pos:self.current]
        value = text[1:-1]
        self.tokens.append(Token(TokenType.STRING_LITERAL, text, start_line, start_col, value))

    def multiline_comment(self):
        nesting = 1

        while nesting > 0 and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
                self.advance()
            elif self.peek() == '*' and self.peek_next() == '/':
                self.advance()
                self.advance()
                nesting -= 1
            elif self.peek() == '/' and self.peek_next() == '*':
                self.advance()
                self.advance()
                nesting += 1
            else:
                self.advance()

        if nesting > 0:
            self.error("Незавершённый многострочный комментарий")

    def advance(self):
        self.current += 1
        self.column += 1
        return self.source[self.current - 1]

    def match(self, expected):
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def peek(self):
        return '\0' if self.is_at_end() else self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def is_at_end(self):
        return self.current >= len(self.source)

    def add_token(self, token_type):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, self.line, self.column - len(text)))

    def error(self, message):
        self.errors.append(f"Ошибка на {self.line}:{self.column}: {message}")
        text = self.source[self.start:self.current] if self.current > self.start else ""
        self.tokens.append(Token(TokenType.ERROR, text, self.line, self.column - len(text), message))

    def has_errors(self):
        return len(self.errors) > 0


def tokenize(source: str):
    scanner = Scanner(source)
    return scanner.tokens


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='Исходный файл')
    parser.add_argument('--output', '-o', help='Выходной файл')
    args = parser.parse_args()

    with open(args.file, 'r', encoding='utf-8') as f:
        source = f.read()

    scanner = Scanner(source)

    out = sys.stdout
    if args.output:
        out = open(args.output, 'w', encoding='utf-8')

    for token in scanner.tokens:
        print(token, file=out)

    if args.output:
        out.close()

    if scanner.has_errors():
        print("\nОшибки:", file=sys.stderr)
        for error in scanner.errors:
            print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
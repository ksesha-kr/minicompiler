from typing import List, Any, Optional
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
        self.tokens: List[Token] = []
        self.errors: List[str] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_column = 1
        self._scan_tokens()

    def _scan_tokens(self):
        while not self._is_at_end():
            self.start = self.current
            self.start_column = self.column
            self._scan_token()

        eof_line = self.line
        eof_col = self.column

        if self.column != 1:
            eof_line += 1
            eof_col = 1

        self.tokens.append(Token(TokenType.END_OF_FILE, "", eof_line, eof_col))

    def _scan_token(self):
        c = self._advance()

        if c == ' ' or c == '\r' or c == '\t':
            pass
        elif c == '\n':
            self.line += 1
            self.column = 1
            return

        elif c == '/':
            if self._match('/'):
                while self._peek() != '\n' and not self._is_at_end():
                    self._advance()
            elif self._match('*'):
                self._multiline_comment()
            else:
                self._add_token(TokenType.OP_DIV)

        elif c == '+':
            self._add_token(TokenType.OP_PLUS)
        elif c == '-':
            if self._peek().isdigit():
                self._scan_negative_number()
            else:
                self._add_token(TokenType.OP_MINUS)
        elif c == '*':
            self._add_token(TokenType.OP_MUL)
        elif c == '%':
            self._add_token(TokenType.OP_MOD)
        elif c == '(':
            self._add_token(TokenType.LPAREN)
        elif c == ')':
            self._add_token(TokenType.RPAREN)
        elif c == '{':
            self._add_token(TokenType.LBRACE)
        elif c == '}':
            self._add_token(TokenType.RBRACE)
        elif c == '[':
            self._add_token(TokenType.LBRACKET)
        elif c == ']':
            self._add_token(TokenType.RBRACKET)
        elif c == ';':
            self._add_token(TokenType.SEMICOLON)
        elif c == ',':
            self._add_token(TokenType.COMMA)

        elif c == '.':
            self._add_token(TokenType.DOT)

        elif c == '=':
            if self._match('='):
                self._add_token(TokenType.OP_EQ)
            else:
                self._add_token(TokenType.OP_ASSIGN)
        elif c == '!':
            if self._match('='):
                self._add_token(TokenType.OP_NE)
            else:
                self._add_token(TokenType.OP_NOT)
        elif c == '<':
            if self._match('='):
                self._add_token(TokenType.OP_LE)
            else:
                self._add_token(TokenType.OP_LT)
        elif c == '>':
            if self._match('='):
                self._add_token(TokenType.OP_GE)
            else:
                self._add_token(TokenType.OP_GT)
        elif c == '&':
            if self._match('&'):
                self._add_token(TokenType.OP_AND)
            else:
                self._error(c, "Недопустимый символ '&'")
        elif c == '|':
            if self._match('|'):
                self._add_token(TokenType.OP_OR)
            else:
                self._error(c, "Недопустимый символ '|'")

        elif c == '"':
            self._scan_string()

        elif c.isdigit():
            self._scan_number()

        elif c.isalpha() or c == '_':
            self._scan_identifier()

        else:
            self._error(c, f"Недопустимый символ '{c}'")

    def _scan_negative_number(self):
        while self._peek().isdigit():
            self._advance()

        is_float = False
        if self._peek() == '.':
            next_char = self._peek_next()
            if next_char.isdigit():
                is_float = True
                self._advance()
                while self._peek().isdigit():
                    self._advance()

                if self._peek() == '.':
                    while True:
                        p = self._peek()
                        if p.isspace() or p in ';\n\r\t(){}[],+-*/%=&|!<>':
                            break
                        if p == '\0': break
                        self._advance()
                    text = self.source[self.start:self.current]
                    self._error(text, f"Некорректное число: '{text}'")
                    return
            elif next_char == '.':
                pass
            else:
                is_float = True
                self._advance()

        text = self.source[self.start:self.current]

        if is_float:
            try:
                val = float(text)
                self.tokens.append(Token(TokenType.FLOAT_LITERAL, text, self.line, self.start_column, val))
            except ValueError:
                self._error(text, f"Некорректное число: '{text}'")
        else:
            self._add_int_token(text, self.line, self.start_column)

    def _scan_identifier(self):
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()

        text = self.source[self.start:self.current]

        if len(text) > 255:
            self.errors.append(f"Ошибка на {self.line}:{self.start_column}: Слишком длинный идентификатор")
            self.tokens.append(
                Token(TokenType.IDENTIFIER, text, self.line, self.start_column, "Слишком длинный идентификатор"))
            return

        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    def _scan_number(self):
        start_line = self.line
        start_col = self.start_column

        while self._peek().isdigit():
            self._advance()

        if self._peek() == '.':
            next_char = self._peek_next()

            if next_char.isdigit():
                self._advance()
                while self._peek().isdigit():
                    self._advance()

                if self._peek() == '.':
                    while True:
                        p = self._peek()
                        if p.isspace() or p in ';\n\r\t(){}[],+-*/%=&|!<>':
                            break
                        if p == '\0': break
                        self._advance()

                    text = self.source[self.start:self.current]
                    self._error(text, f"Некорректное число: '{text}'")
                    return

                text = self.source[self.start:self.current]
                try:
                    value = float(text)
                    self.tokens.append(Token(TokenType.FLOAT_LITERAL, text, start_line, start_col, value))
                except ValueError:
                    self._error(text, f"Некорректное число: '{text}'")
                return

            elif next_char == '.':
                text = self.source[self.start:self.current]
                self._add_int_token(text, start_line, start_col)

                dot_col = self.column
                self.tokens.append(Token(TokenType.DOT, ".", self.line, dot_col))

                self._advance()

                if not self._is_at_end():
                    self.current += 1

                return

            else:
                self._advance()
                text = self.source[self.start:self.current]
                try:
                    value = float(text)
                    self.tokens.append(Token(TokenType.FLOAT_LITERAL, text, start_line, start_col, value))
                except ValueError:
                    self._error(text, f"Некорректное число: '{text}'")
                return

        text = self.source[self.start:self.current]
        self._add_int_token(text, start_line, start_col)

    def _add_int_token(self, text: str, line: int, col: int):
        try:
            val = int(text)
            min_val = -2 ** 31
            max_val = 2 ** 31 - 1

            if val < min_val or val > max_val:
                self._error(text, f"Целочисленный литерал {val} вне допустимого диапазона [-2³¹, 2³¹-1]")
            else:
                self.tokens.append(Token(TokenType.INT_LITERAL, text, line, col, val))
        except ValueError:
            self._error(text, f"Некорректное число: '{text}'")

    def _scan_string(self):
        start_line = self.line
        start_col = self.start_column

        while not self._is_at_end():
            c = self._peek()
            if c == '\n':
                break
            if c == '"':
                break
            self._advance()

        if self._is_at_end() or self._peek() == '\n':
            text = self.source[self.start:self.current]
            text = text.replace('"', '\\"')
            self._error(text, "Незавершённая строка")
            return

        self._advance()
        text = self.source[self.start:self.current]
        value = text[1:-1]
        self.tokens.append(Token(TokenType.STRING_LITERAL, text, start_line, start_col, value))

    def _multiline_comment(self):
        nesting = 1
        comment_start_line = self.line
        comment_start_col = self.start_column

        while nesting > 0 and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
                self.column = 1
                self._advance()
            elif self._peek() == '*' and self._peek_next() == '/':
                self._advance()
                self._advance()
                nesting -= 1
            elif self._peek() == '/' and self._peek_next() == '*':
                self._advance()
                self._advance()
                nesting += 1
            else:
                self._advance()

        if nesting > 0:
            text = self.source[self.start:self.current]
            self.errors.append(
                f"Ошибка на {comment_start_line}:{comment_start_col}: Незавершённый многострочный комментарий")
            self.tokens.append(Token(TokenType.ERROR, "", comment_start_line, comment_start_col,
                                     "Незавершённый многострочный комментарий"))

    def _advance(self):
        if self._is_at_end():
            return '\0'
        self.current += 1
        self.column += 1
        return self.source[self.current - 1]

    def _match(self, expected):
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _peek(self):
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _is_at_end(self):
        return self.current >= len(self.source)

    def _add_token(self, token_type: TokenType, value: Any = None):
        text = self.source[self.start:self.current]
        col = self.start_column
        self.tokens.append(Token(token_type, text, self.line, col, value))

    def _error(self, text_or_char: str, message: str):
        lexeme = text_or_char
        col = self.start_column

        self.errors.append(f"Ошибка на {self.line}:{col}: {message}")
        self.tokens.append(Token(TokenType.ERROR, lexeme, self.line, col, message))

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

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Файл {args.file} не найден", file=sys.stderr)
        sys.exit(1)

    scanner = Scanner(source)

    out = sys.stdout
    if args.output:
        out = open(args.output, 'w', encoding='utf-8')

    for token in scanner.tokens:
        print(token, file=out)

    if args.output:
        out.close()

    if scanner.has_errors():
        for error in scanner.errors:
            print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

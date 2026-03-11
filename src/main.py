import sys
import argparse
import json
from pathlib import Path

from src.lexer.scanner import Scanner
from src.parser.parser import Parser, ParseError


def cmd_lex(args):
    with open(args.input, 'r', encoding='utf-8') as f:
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
        print("\nОшибки лексера:", file=sys.stderr)
        for error in scanner.errors:
            print(error, file=sys.stderr)
        return 1

    return 0


def cmd_parse(args):
    with open(args.input, 'r', encoding='utf-8') as f:
        source = f.read()

    scanner = Scanner(source)

    if scanner.has_errors():
        print("Ошибки лексера:", file=sys.stderr)
        for error in scanner.errors:
            print(error, file=sys.stderr)
        return 1

    parser = Parser(scanner.tokens)
    ast = parser.parse()

    out = sys.stdout
    if args.output:
        out = open(args.output, 'w', encoding='utf-8')

    if args.ast_format == 'text':
        print(ast.__str__(), file=out)
    elif args.ast_format == 'json':
        print(json.dumps(ast.to_dict(), indent=2, ensure_ascii=False), file=out)
    elif args.ast_format == 'dot':
        print(_ast_to_dot(ast), file=out)

    if args.output:
        out.close()

    if parser.errors:
        print("\nОшибки парсера:", file=sys.stderr)
        for error in parser.errors:
            print(error, file=sys.stderr)
        return 1

    return 0


def _ast_to_dot(ast) -> str:
    lines = []
    lines.append("digraph AST {")
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box];")
    lines.append("")

    node_id = [0]

    def visit(node, parent_id=None):
        current_id = node_id[0]
        node_id[0] += 1

        node_type = type(node).__name__
        label = node_type

        if hasattr(node, 'name'):
            label += f"\\n{node.name}"
        if hasattr(node, 'var_type'):
            label += f"\\n{node.var_type}"
        if hasattr(node, 'operator'):
            label += f"\\n{node.operator}"
        if hasattr(node, 'value') and node.value is not None:
            label += f"\\n{node.value}"
        if hasattr(node, 'return_type'):
            label += f"\\n-> {node.return_type}"

        label += f"\\n[line {node.line}]"

        color = "white"
        if node_type.endswith("ExprNode") or node_type.endswith("Expr"):
            color = "lightblue"
        elif node_type.endswith("StmtNode") or node_type.endswith("Stmt"):
            color = "lightgreen"
        elif node_type.endswith("DeclNode") or node_type.endswith("Decl"):
            color = "lightyellow"
        elif node_type == "ProgramNode":
            color = "lightgray"

        lines.append(f'  node{current_id} [label="{label}", style=filled, fillcolor={color}];')

        if parent_id is not None:
            lines.append(f'  node{parent_id} -> node{current_id};')

        children_attrs = ['declarations', 'statements', 'parameters', 'fields',
                          'left', 'right', 'operand', 'arguments', 'target', 'value',
                          'condition', 'then_branch', 'else_branch', 'body',
                          'init', 'update', 'callee']

        for attr in children_attrs:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child is not None:
                    if isinstance(child, list):
                        for c in child:
                            if hasattr(c, 'line'):
                                visit(c, current_id)
                    elif hasattr(child, 'line'):
                        visit(child, current_id)

        return current_id

    visit(ast)
    lines.append("}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog='minicompiler',
        description='MiniCompiler - учебный компилятор'
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    lex_parser = subparsers.add_parser('lex', help='Лексический анализ')
    lex_parser.add_argument('--input', '-i', required=True, help='Входной файл')
    lex_parser.add_argument('--output', '-o', help='Выходной файл')

    parse_parser = subparsers.add_parser('parse', help='Синтаксический анализ')
    parse_parser.add_argument('--input', '-i', required=True, help='Входной файл')
    parse_parser.add_argument('--output', '-o', help='Выходной файл')
    parse_parser.add_argument(
        '--ast-format', '-f',
        choices=['text', 'json', 'dot'],
        default='text',
        help='Формат вывода AST'
    )
    parse_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Подробный вывод'
    )

    args = parser.parse_args()

    if args.command == 'lex':
        sys.exit(cmd_lex(args))
    elif args.command == 'parse':
        sys.exit(cmd_parse(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
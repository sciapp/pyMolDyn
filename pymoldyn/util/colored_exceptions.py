import sys


def excepthook(type, value, tb):
    import traceback

    from pygments import highlight
    from pygments.formatters import TerminalFormatter
    from pygments.lexers import get_lexer_by_name
    from pygments.token import Token

    tbtext = "".join(traceback.format_exception(type, value, tb))

    lexer = get_lexer_by_name("pytb", stripall=True)

    formatter = TerminalFormatter(bg="dark")  # dark or light
    formatter.colorscheme[Token.Literal.Number] = ("yellow", "yellow")

    sys.stderr.write(highlight(tbtext, lexer, formatter))


sys.excepthook = excepthook

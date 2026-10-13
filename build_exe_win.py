"""Build MenuMaker.exe tren Windows.

Python 3.10.0 bi loi trinh bien dich khien `dis.get_instructions()` bao
IndexError khi phan tich mot so module (vi du PIL/Image.py). Loi nay chi
anh huong buoc phan tich cua PyInstaller, khong anh huong luc chay.

Script nay thay bo giai ma bytecode cua PyInstaller bang mot bo giai ma
thu cong (khong dung `dis.get_instructions`) roi moi goi PyInstaller.
"""
from __future__ import annotations

import dis
import inspect

from PyInstaller.lib.modulegraph import util


def _argval(co, op, arg, offset):
    if arg is None:
        return None
    if op in dis.hasconst:
        return co.co_consts[arg]
    if op in dis.hasname:
        return co.co_names[arg]
    if op in dis.haslocal:
        return co.co_varnames[arg]
    if op in dis.hasfree:
        return (co.co_cellvars + co.co_freevars)[arg]
    if op in dis.hascompare:
        return dis.cmp_op[arg]
    if op in dis.hasjrel:
        return offset + 2 + arg
    if op in dis.hasjabs:
        return arg
    return arg


class _Instr(tuple):
    __slots__ = ()

    def __new__(cls, offset, opname, opcode, arg, argval):
        return tuple.__new__(cls, (offset, opname, opcode, arg, argval))

    offset = property(lambda s: s[0])
    opname = property(lambda s: s[1])
    opcode = property(lambda s: s[2])
    arg = property(lambda s: s[3])
    argval = property(lambda s: s[4])


def _manual_instructions(co):
    code = co.co_code
    n = len(code)
    i = 0
    extended = 0
    while i < n:
        op = code[i]
        if op >= dis.HAVE_ARGUMENT:
            arg = code[i + 1] | extended
            extended = 0
            if op == dis.EXTENDED_ARG:
                extended = arg << 8
        else:
            arg = None
            extended = 0
        name = dis.opname[op]
        if name != "EXTENDED_ARG":
            try:
                av = _argval(co, op, arg, i)
            except (IndexError, TypeError):
                av = arg
            yield _Instr(i, name, op, arg, av)
        i += 2


def _iterate_instructions(code_object):
    yield from _manual_instructions(code_object)
    yield None
    for constant in code_object.co_consts:
        if inspect.iscode(constant):
            yield from _iterate_instructions(constant)


util.iterate_instructions = _iterate_instructions


def main():
    from PyInstaller.__main__ import run

    run([
        "app.py",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "MenuMaker",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "PIL._tkinter_finder",
        "--exclude-module", "numpy",
        "--exclude-module", "pytest",
        "--exclude-module", "matplotlib",
    ])


if __name__ == "__main__":
    main()

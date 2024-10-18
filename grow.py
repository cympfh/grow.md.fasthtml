#!/usr/bin/env python3

import glob
import logging
import subprocess

import click
from fasthtml.common import (
    A,
    Aside,
    Body,
    Div,
    FastHTML,
    Li,
    Link,
    NotStr,
    P,
    Script,
    Section,
    Style,
    Title,
    Ul,
    serve,
)
import starlette.requests

logger = logging.getLogger("uvicorn")


def make():
    bulma = Link(
        rel="stylesheet",
        href="https://cdn.jsdelivr.net/npm/bulma@1.0.2/css/bulma.min.css",
    )
    font_awesome = Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css",
        integrity="sha512-Kc323vGBEqzTmouAECnVceyQqyqdsSiqLQISBL29aUW4U/M7pSPA/gEUZQqv1cwx4OnYxTxve5UMg5GT6L4JJg==",
        crossorigin="anonymous",
        referrerpolicy="no-referrer",
    )
    mathjax = Script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js")
    my_css = (
        Style("""
i.fa-regular {
    width: 1.5rem;
    text-align: center;
}
"""),
    )
    return FastHTML(hdrs=(my_css, bulma, font_awesome, mathjax), live=True)


class Path:
    """
    File (markdown)
        a.md
        a/b.mkd
        a/b/c.md
    Directory
        a
        a/b
    """

    path: str
    is_dir: bool
    is_file: bool

    def __init__(self, pathstr: str):
        p = pathstr.removeprefix("/").removesuffix("/")
        if p == "":
            self.path = "."
            self.set_dir()
        elif p.endswith(".md") or p.endswith(".mkd"):
            self.path = p
            self.set_file()
        else:
            self.path = p
            self.set_dir()

    def parent(self):
        """親ディレクトリを返す

        - ファイルなら親ディレクトリ
        - ディレクトリなら自身を返す
        """
        if self.is_dir:
            return self
        return Path("/".join(self.path.split("/")[:-1]))

    def set_dir(self):
        self.is_dir = True
        self.is_file = False

    def set_file(self):
        self.is_dir = False
        self.is_file = True

    def __str__(self) -> str:
        if self.is_file:
            return self.path
        else:
            return f"{self.path}/"

    def __repr__(self) -> str:
        return f"Path(path={self.path}, is_file={self.is_file}, is_dir={self.is_dir})"


class FileSystem:
    @staticmethod
    def filelist(path: Path) -> list[Path]:
        """markdown へのパス一覧を返す

        grow root からの相対パスで返す

        - 直下の markdown 一覧
        - markdown を含むディレクトリ一覧

        Parameters
        ----------
        path
            ディレクトリへのパス
            この下を見る
        """
        ls = []
        ls += glob.glob("**/*.md", root_dir=str(path), recursive=True)
        ls += glob.glob("**/*.mkd", root_dir=str(path), recursive=True)
        ls = [f"{p.split("/")[0]}/" if "/" in p else p for p in ls]
        ls = [".."] + sorted(set(ls))
        ls = [Path(p) for p in ls]
        logger.info("filelist: %s => %s", path, ls)
        return ls


def folder(path: Path):
    """フォルダ内をレンダリングする

    Parameters
    ----------
    path
        ファイルまたはディレクトリへのパス
        ファイルパスの場合はそれがあるフォルダを見る
    """

    def link(path: Path):
        if path.is_file:
            icon = '<i class="fa-regular fa-file"></i>'
        else:
            icon = '<i class="fa-regular fa-folder"></i>'
        return A(NotStr(icon), path, href=str(path))

    ls = FileSystem.filelist(path.parent())
    return Aside(Ul(*[Li(link(path)) for path in ls], cls="menu-list"), cls="menu")


def compile(path: Path) -> tuple[int, str, str]:
    """markdown をコンパイルする

    Returns
    -------
    status
    stdout
    stderr
    """
    proc = subprocess.run(["unidoc", str(path)], capture_output=True)
    return (proc.returncode, proc.stdout.decode(), proc.stderr.decode())


def content(path: Path):
    """markdown をレンダリングして返す

    Parameters
    ----------
    path
        markdown へのファイルパス
        またはそれ以外のパス

    Returns
    -------
    path がファイルパスのときは markdown ファイルだとして HTML レンダリングする
    """
    if not path.is_file:
        return Div(
            f"{path}",
            cls="notification is-info",
        )
    statuscode, stdout, stderr = compile(path)
    if statuscode == 0:
        return Div(NotStr(stdout), cls="content")
    return Div(stderr, cls="notification is-danger")


def render(req: starlette.requests.Request):
    path = Path(req.url.path)
    logger.info("path: %s", path)
    hero = Section(
        Div(P(path, cls="title"), cls="hero-body"),
        cls="hero",
    )
    section = Div(
        Div(
            Div(
                Div(folder(path), cls="column is-two-fifths"),
                Div(content(path), cls="column"),
                cls="columns",
            ),
            cls="container",
        ),
        cls="section",
    )
    return (
        Title(f"{path} - grow.md"),
        Body(hero, section),
    )


app = make()


@app.route("/{_a}")
def get_1(req: starlette.requests.Request):
    return render(req)


@app.route("/{_a}/{_b}")
def get_2(req: starlette.requests.Request):
    return render(req)


@app.route("/{_a}/{_b}/{_c}")
def get_3(req: starlette.requests.Request):
    return render(req)


@app.route("/{_a}/{_b}/{_c}/{_d}")
def get_4(req: starlette.requests.Request):
    return render(req)


@click.command
@click.option("--port", "-p", type=int, default=8080)
def main(port: int):
    serve(port=port)


if __name__ == "__main__":
    main()

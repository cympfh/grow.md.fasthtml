#!/usr/bin/env python3

import click
import glob
import logging
import subprocess

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


def filelist(path: str) -> list[str]:
    """markdown へのパス一覧を返す

    - 直下の markdown 一覧
    - markdown を含むディレクトリ一覧

    Parameters
    ----------
    path
        ディレクトリへのパス
        この下を見る
    """
    ls = glob.glob("**/*.md", root_dir=path, recursive=True)
    logger.info("filelist: %s => %s", path, ls)
    return ["../"] + sorted(
        set(f"{path.split("/")[0]}/" if "/" in path else path for path in ls)
    )


def folder(path: str):
    """フォルダ内をレンダリングする

    Parameters
    ----------
    path
        ファイルまたはディレクトリへのパス
        ファイルパスの場合はそれがあるフォルダを見る
    """

    def parent(path: str) -> str:
        fs = path.split("/")[:-1]
        return "/".join(fs)

    def link(path):
        is_file = path.endswith(".md") or path.endswith(".mkd")
        if is_file:
            icon = '<i class="fa-regular fa-file"></i>'
        else:
            icon = '<i class="fa-regular fa-folder"></i>'
        return A(NotStr(icon), path, href=f"./{path}")

    ls = filelist(parent(path))
    return Aside(Ul(*[Li(link(path)) for path in ls], cls="menu-list"), cls="menu")


def compile(path: str) -> tuple[int, str, str]:
    """markdown をコンパイルする

    Returns
    -------
    status
    stdout
    stderr
    """
    proc = subprocess.run(["unidoc", path], capture_output=True)
    return (proc.returncode, proc.stdout.decode(), proc.stderr.decode())


def content(path: str):
    is_file = path.endswith(".md") or path.endswith(".mkd")
    if not is_file:
        return Div(
            f"{path}",
            cls="notification is-info",
        )

    statuscode, stdout, stderr = compile(path)
    if statuscode == 0:
        return Div(NotStr(stdout), cls="content")

    return Div(stderr, cls="notification is-danger")


def render(req: starlette.requests.Request):
    path = req.url.path.removeprefix("/")
    is_file = path.endswith(".md") or path.endswith(".mkd")
    if not is_file:
        path = path.removesuffix("/") + "/"
    logger.info("path: %s (is_file=%s)", path, is_file)
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

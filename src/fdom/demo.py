from fdom.basecompiler import html


def demo():
    title_level = 1
    title_style = {"color": "blue"}
    body_style = {"color": "red"}

    paragraphs = {
        "First Title": "Lorem ipsum dolor sit amet. Aut voluptatibus earum non facilis mollitia.",
        "Second Title": "Ut corporis nemo in consequuntur galisum aut modi sunt a quasi deleniti.",
    }

    html_paragraphs = [
        html"""
            <h1 { {"style": title_style} }>{title}</{...}>
            <p { {"style": body_style} }>{body}</p>
        """
        for title, body in paragraphs.items()
    ]

    def simple_wrapper(*children):
        return html'<div class="simple-wrapper">{children}</div>'

    result = html"<{simple_wrapper}>{html_paragraphs}</{simple_wrapper}>"
    print(result)


if __name__ == "__main__":
    # demo()  - need full support for parsing interpolation placement
    tag = 'h1'
    title_style = {'a': 47, 'b': 'bar'}
    title = 'Some Title'
    print(html'<div>1</div>')
    # print(html'<{tag}><body baz="fum"><h1 {title_style!r:dict}>Blah {title:str}, foo</h1></body></{tag}>')
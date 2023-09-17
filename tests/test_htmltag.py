from fdom.htmltag import html, html_iter


def test_simple():
    text = "arbitrary text"
    assert list(html_iter"<div>Include some {text}</div>") == [
        '<div>Include some ', 'arbitrary text', '</div>'
    ]


def test_listing():

    def Todo(prefix, label):
        return html'<li>{prefix}: {label}</li>'

    assert Todo('High', 'Get milk') == '<li>High: Get milk</li>'

    def TodoList(prefix, todos):
        return html'<ul>{[Todo(prefix, label) for label in todos]}</ul>'

    assert TodoList('High', ['Get milk']) == '<ul><li>High: Get milk</li></ul>'

    b = html"""<html>
        <body attr=blah" yo={1}>
            {TodoList('High', ['Get milk', 'Change tires'])}
        </body>
    </html>"""

    assert b == """<html>
        <body attr="blah"">
            <ul><li>High: Get milk</li><li>High: Change tires</li></ul>
        </body>
    </html>"""

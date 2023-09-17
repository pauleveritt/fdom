from fdom.htmltag import html, html_iter


def test_simple():
    text = "arbitrary text"
    assert list(html_iter"<div>Include some {text}</div>") == [
        '<div>Include some ', 'arbitrary text', '</div>'
    ]


def Todo(prefix, label):
    return html'<li>{prefix}: {label}</li>'


def TodoList(prefix, todos):
    return html'<ul>{(Todo(prefix, label) for label in todos)}</ul>'


def test_listing():
    assert Todo('High', 'Get milk & eggs') == '<li>High: Get milk &amp; eggs</li>'
    assert TodoList('High', ['Get milk & eggs']) == '<ul><li>High: Get milk &amp; eggs</li></ul>'

    b = html"""<html>
        <body attr="blah" yo={1}>
            {TodoList('High', ['Get milk', 'Change tires'])}
        </body>
    </html>"""

    # FIXME what happened to yo={1} ?
    assert b == """<html>
        <body attr="blah">
            <ul><li>High: Get milk</li><li>High: Change tires</li></ul>
        </body>
    </html>"""


# FIXME can this use of html_iter vs html be parameterized?

def TodoIter(prefix, label):
    return html_iter'<li>{prefix}: {label}</li>'


def TodoListIter(prefix, todos):
    return html_iter'<ul>{[TodoIter(prefix, label) for label in todos]}</ul>'


def test_listing_iter():
    assert list(TodoIter('High', 'Get milk & eggs')) == ['<li>', 'High', ': ', 'Get milk &amp; eggs', '</li>']
    assert list(TodoListIter('High', ['Get milk & eggs'])) == ['<ul>', '<li>', 'High', ': ', 'Get milk &amp; eggs', '</li>', '</ul>']

    b = list(html_iter"""<html>
        <body attr="blah" yo={1}>
            {TodoListIter('High', ['Get milk', 'Change tires'])}
        </body>
    </html>""")

    # FIXME what happened to yo={1} ?
    assert ''.join(b) == """<html>
        <body attr="blah">
            <ul><li>High: Get milk</li><li>High: Change tires</li></ul>
        </body>
    </html>"""


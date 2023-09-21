from fdom.htmltag import html, html_iter, HTML


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

    assert b == """<html>
        <body attr="blah" yo="1">
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
        <body attr="blah" yo="1">
            <ul><li>High: Get milk</li><li>High: Change tires</li></ul>
        </body>
    </html>"""


def test_sanitize():
    # NOTE this string is not encoded with the html tag, which is used for
    # source code, instead this is supposed to be representative of user
    # input that is used maliciously for an injection attempt (XSS).
    # Example from https://en.wikipedia.org/wiki/Cross-site_scripting
    injection_attempt = '<script>alert("xss");</script>'

    assert html'<div>Here is your query: {injection_attempt}</div>' == \
        '<div>Here is your query: &lt;script&gt;alert(&quot;xss&quot;);&lt;/script&gt;</div>'

    assert html'<div attr="{injection_attempt}">Hello, world!</div>' == \
        '<div attr="&lt;script&gt;alert(&quot;xss&quot;);&lt;/script&gt;">Hello, world!</div>'


def test_respect_html_marker():
    # Using HTML assures that the text is valid HTML as-is. Use carefully!
    arbitrary_html = HTML('<script>alert("No worries");</script>')
    assert html'<div>Here is an embedded script: {arbitrary_html}</div>' == \
        '<div>Here is an embedded script: <script>alert("No worries");</script></div>'


def test_dynamic_attribute():
    # NOTE this is probably correct HTML, but it should be doublechecked!
    action = 'click'
    alert = HTML('alert("Clicked!");')
    assert html'<div on{action}="{alert}"/>' == \
        '<div onclick="alert(&quot;Clicked!&quot;);"></div>'

from fdom.astparser import as_ast, Tag, Interpolation
from fdom.htmlcompiler import HTMLCompiler
from fdom.thunky import Chunk, Thunk, convert_to_proposed_scheme


def html(*args):
    return args


# template: Tag = as_ast"<h{level}>some text</h{level}>"

template = Tag(tagname=None, attrs=[], children=[Tag(tagname=['h', Interpolation(1, None, None)], attrs=[], children=['some text'])])
compiler = HTMLCompiler()
cls = compiler(template.children[0])
print(compiler.code)

level = 4
args = convert_to_proposed_scheme(*html"<h{level}>some text</h{level}>")
print(f'{args=}')
it = cls(args)
print(''.join(list(it)))

exit()

template2 = Tag(tagname=None, attrs=[], children=[Tag(tagname=['h1'], attrs=[], children=['some text'])])
compiler = HTMLCompiler()
compiler.compile(template2.children[0])
print(compiler.code)


template3 = Tag(tagname=None, attrs=[], children=[
    Tag(tagname=['h1'], attrs=[], children=[
        'starting text',
        Tag(tagname=['div'], attrs=[(['blink'], ['on']), (['disabled'], None)], children=['in this div']),
        'ending text'])])
compiler = HTMLCompiler()
compiler.compile(template3.children[0])
print(compiler.code)

template4 = Tag(tagname=None, attrs=[], children=[
    Tag(tagname=['h1'], attrs=[], children=[
        'starting text',
        Tag(tagname=['div'], attrs=[(['blink'], ['on']), (['disabled'], None), ([Interpolation(42, None, None)], None)], children=['in this div']),
        'ending text'])])
compiler = HTMLCompiler()
compiler.compile(template4.children[0])
print(compiler.code)

template5 = Tag(tagname=None, attrs=[], children=[
    Tag(tagname=['h1'], attrs=[], children=[
        'starting text',
        Tag(tagname=['div'], attrs=[(['on', Interpolation(42, None, None)], ['foobar_code()'])], children=['in this div']),
        'ending text'])])
compiler = HTMLCompiler()
print(compiler(template5.children[0]))


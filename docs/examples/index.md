# Examples

Let's take a look at some common templating patterns, implemented in `fdom`.

## Listing

```{toctree}
---
maxdepth: 1
---
static_string
variables
expressions
conditionals
looping
components
```

## Questions for Jim

### Immediately rendering vs. returning a vdom

`viewdom` returns a vdom for the `html""` operation. It's a second step to render it. `fdom` returns a string. You have
to use `as_ast` if you want the intermediate representation.

What does it mean when a subcomponent is rendered into a parent? Will we only get the string representation?

Would it make more sense for `html""` to return a `Tag` whose `__str__` protocol did the rendering?

### Boolean collapsing

`htm.py` (and thus `viewdom`) can do this: `<div editable={True}>Hello World</div>` -> `"<div editable>Hello World</div>"`


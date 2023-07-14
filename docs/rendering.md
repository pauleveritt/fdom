# Rendering

Websites send HTML. Systems use views, templates, and re-usable macros/shortcuts/components to do so.

If rendering can be brought "into the system", we can get tremendous benefits:

- Performance through fine-grained changes
- Extensibility through replaceable pieces
- Trust through reliable persistence

# Templates

A template is a DSL which is used to process inputs into 

# Component

A component is the finest-grain of rendering. It is a callable which takes information and returns a VDOM.



- Components, templates, views
- As effects
- Results are stored
- Patchable
- Registered against symbol
- Very testable
- Portable between systems
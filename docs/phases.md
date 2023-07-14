# Build Phases

We want a very fast build system:

- If work fails half-way through, we don't want to repeat that work when fixed
- We want *coherent* parallelism
- Sets of activities are conceptually related

Like Sphinx, Gatsby, and others, this system will have a sequence of phases.

## Change handlers

Changes in a phase produce work in the next phases. You can think of this as push-style, or think of it as observables.
Either way: handlers can register "dependencies". These dependencies are documents in the database. When those documents
change, a trigger (or a query) determines the work to do, finds change handlers, and runs them. Which produces changes,
which triggers dependencies, etc.

This system aims for "fine-grained changes." When a change happens, the system tries to find the best handler(s). If a
fine-grained handler can't be found or used, we play it safe and do a "full" rebuild (but only for that entity.)

But hopefully a handler can be fine-grained. For example, a Sphinx link can use the title of the target as the link
text. Thus, the link has a dependency on another document. But really, only on the value of the title. If the target's
body changes, you don't need to regenerate the link text.

Thus, we might have a SQL table of dependencies, with dependency types such as `Link`. "Link" rows in that table can
optionally say what attribute they are watching. Later, when the resource changes, the change handler runs, extracts the
title, and sees it hasn't changed. The change propagation would then stop and no dependencies notified.

Change handlers might also be "fine-grained" in applying updates. Consider the same case: a document links to another.
The title changes. Do we *really* need to re-run the parsing of the Markdown document? The rendering of the parsed
Markdown? The view template which generates an output?

Imagine instead that all of those build artifacts were stored in the database as JSON. The link was the parsed Markdown
as `Link(ref="/folder1/doc2", attr="title", value="Doc2 Title")`. The change handler for `/folder1/doc2` could do the
following:

- Grab every `Link` node with `ref` for `/folder1/doc2`
- ...using an index on a computed column which extracts from the JSON
- See which ones looked for `title`
- ...and, the previous value is different from the new value

Once the query found all the out-of-date "observer" nodes, the query could patch it *in place* using [`JSON_PATCH]
(https://database.guide/sqlite-json_patch/). No trip to Python for Markdown rendering needed. The same type of node
might appear in the rendered view. And thus, the value patched in-place without a trip to Python to re-render the view
template.

## A Phase

- Phases are serial
- But work within a phase is parallel
- A phase gets its inputs from the previous phase
- Everything is immutable
- So it is safe to parallelize work within a phase
- Hopefully phases are extensible...a system can add in a phase

## Source Phase

As described in "resources", outside content is read and processed by handlers during a "source" phase. For each entry:

- Calculate a hash
- See if the system already has it, at the path, same hash
- Update if needed
- Detect deletions
- Stores the metadata and contents in JSON document in a table
- It's possible that there is a special "sources" table with the column structure common to all "source" entries

That's for a source that's a file-on-disk. Gatsby has a rich ecosystem of pluggable sources. It can get entities from
GraphQL queries, REST, SQL, etc.

This is work is done in a "sources" build phase. Once all the source entries are reconciled, a transaction is committed.
This then triggers work in the next phase: transform.

As a note: this could actually run "in-core". Meaning, in the database. There are SQlite extensions which can read
files. Presumably they could use the `awatch` package's crate, running in a thread, to "watch" for changes. Then, update
the database without a trip to Python.

## Transform

A `.md` file generates a source document. But it then needs to be transformed. For example, by a Markdown processor.
This becomes an important part of the system to get right:

- Bail early if something goes wrong
- Lots of formats so extensibility is key
- Pre- and post- handlers (kind of like middleware) for small customization chains

The result is...an JSON document. Each transformed source produces an intermediate representation. It needs to be
storable as JSON (or a blob.) And it needs to be identifiable by a symbol which can find the right handler and hand off
to the next phase.

## Resource

This is where a fork in the road might happen. Resources are content. Perhaps with a standard common schema (e.g. Dublin
Core.) But certainly with resource types.

For example, the frontmatter in a Markdown document might indicate that this document is an Invoice. The other keys in
the frontmatter will provide the metadata, and the Markdown body as the content.

During this process, the content might be validated against a schema (e.g. via Pydantic.)

Images are another kind of resource. They won't have the same core metadata. But they will exist at a URL, be linkable,
and the like. Images are a VERY important piece of the puzzle, and the system has be designed with them in mind. Image
processing can consume huge percentages of build time.

When the resource instance is created, it is seated in the "resource tree": a hierarchy as on disk or in a URL space.

## Assets (parallel with Resource phase)

Other transformed inputs, though, aren't "content". But they affect many parts of the downstream system.

For example: configuration information. For example, the contents of `conf.py`. A representation needs to be stored in
the system, to let it "observe" changes to configuration. Anything that depended on a configuration value would be
tracked. If that value changed, the change handler system would kick in.

In fact, this applies to software as well. If a component is used to render some data, the rendered artifact is stored.
But the artifact depends on the component definition in Python. If the file changes, anything that depended on it should
be rebuilt. Thus, we need a document node representing the component's software.

## Resolving

Resource might link to other resources -- in Markdown, via "reference" fields in frontmatter, image tags, etc. But in
the first pass through, we might not have all the targets until the end of the build phase. We need another phase to "
resolve" references (as Sphinx does.)

As a note, though we're using SQLite, we can't do joins for this, for two reasons:

- Hypertext links might be numerous, and...
- ...the occur in the JSON body.

Instead, we can maintain the linking information elsewhere. Perhaps in an adjacency list style table, for example. It's
important to get this right: rich linking, with warnings of broken links, is a big value in Sphinx.

Getting it right means:

- Same guarantees as foreign-key linking (meaning, a trigger runs and a transaction aborts on errors)
- Link "types"
- High performance
- Granular changes

## Rendering

At some phase, you want to gather inputs and generate output artifacts: HTML pages, PDF files, images, etc. This is
traditionally the world of templates, views, and reusable components/macros/snippets/shortcuts.

When a resource changes, something needs to mediate the outside world with the rendering. That is the view. It has
inputs and generates the output.

Like the other parts of rendering, a "view" is "registered" against a "symbol". Pyramid (and Zope) were pioneers on
this. This is a resource-oriented framework. You grab a resource in the resource tree and render it, not grab a template
and find data to render.

Views are registered and the system finds the best-fit for rendering. The view can register for a resource, in a certain
path, in a certain set of circumstances. One `Invoice` might use a certain view, but another might be paired with a
different view. A view might be a function (or a dataclass) which gets some values "from the system" injected into it.
It then might return a template.

This applies especially to components, which are the real magic of fine-grained changes. A component -- such
as `Heading` registers in the system. You can then use `<{Heading}>` in a template. But `Heading` is just a symbol.
Multiple
implementations [can be registered](https://hopscotch.readthedocs.io/en/latest/registry.html#registering-things).

When a renderable is registered, it gets into the registry, which is part of "the system", aka the document database. It
can then be an effect that's executed when its dependencies change.

The results of rendering -- whether a fine-grained component, a view, or an image -- are stored in the database in JSON.
These artifacts can be patched to avoid re-rendering.

But they might leave -- in their JSON representation -- small amounts of instructions. Sort of like SSI/ESI --
references to other fragments, to decrease the surface area of final changes.

## Assembly

This final step is a brain-dead string substitution. It can be done "in-core" in the database, no trip to Python. Either
in an extension or possibly SQLite string operations.

The result: a row in a table for every thing that needs to go onto disk. The final result.

## Writing

At some point, you need to write to disk. This is a part where other systems struggle. Since their artifacts are
immediately-written to disk, they can't really tell later if the output directory is out-of-date.

As we just said, the final result -- each set of bytes to write to disk -- is in the database. We just need something
that does like an rsync between the table and disk. It would handle:

- Adding any new artifacts
- Modifying existing artifacts
- Deleting a file on disk if it is no longer "in the system"
- Detecting when a file hasn't changed and doesn't need writing
- Detecting when a file has been modified on disk or deleted, then re-writing

This doesn't have to be in Python. It can be a very fast, "in-core" operation. But it needs to be VERY trustworthy. It
needs to feel like we're extending transaction semantics to a transactional filesystem.
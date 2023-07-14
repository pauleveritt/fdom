# Resources

The outside world has entities -- documents, data, images -- which form the corpus. Like Gatsby, this system will have
duplicate those into a standard, internal representation which drives all the build phases.

## The resource tree

All "content" in the site will be represented in the resource tree (inspired by Zope/Pyramid.) This is a hierarchical
structure. Path resolvers help locate resources quickly, including relative path resolution/formation from any level in
the system.

Because we have a representation of an external *inside* the system, we can then deliver on many contracts, in an
extensible way. This was an innovation of Gatsby.

## A document

Imagine a Markdown document on disk, in an input directory.
The system starts up and discovers all inputs:

- A path
- A hash
- Contents
- Mime type

This representation is then stored "in the system", very quickly, with almost no processing. Gatsby refers to these a
sources and allows registered handlers.

In the first phase of the system, a "source" handler gets this basic information into a document.

In the next phase, a transform then gets and stores a Markdown *parse* structure. Ideally, this structure is aware of
our system. For example, the token stream:

- Can be serialized to/from JSON for persistence
- Static subtrees can be annotated for rendering speedups
- `Link` values can be represented, queried, and patched without re-parsing

Next, another transform takes the (stored) token stream and renders to frontmatter+HTML. In the resource phase, this is
then turned into a document.

Why all this separation? Why store all these intermediate representations?

- We want a *tiny* surface area of change
- Which we can then easily locate
- And tie to the change detection and dependency system
- Finally, if possible, SQL "patch" simple changes without re-processing in Python

## A row

A resource might come from a REST query. Or a row in an Excel spreadsheet. Or a PostgreSQL table row.

All of these "sources" can feed source documents into the system, the be picked up by handlers and processed through the
pipeline.

## An image

Processing images is a key part of making a very performant website. However, image processing is a huge factor in long
build times. The system needs a solid, sustainable way to handle images fast.

SQLite has blob support with lots of information about efficiently storing images. It's tempating to leave them out of
the database. That's a mistake: staying "in the system" is important:

- Self-contained data db files can ship to edge computation
- Transactions you can trust
- The change detection in this system

There are two key ways to improve on the state of the art.

First, pre-generate flavors early. Many of the systems wait until a component or template requests an image. The request
includes the information for transformation: formats, sizes, etc. But this has drawbacks:

- You don't start processing images until late in the build process, when templates start getting applied to data
- Single-threaded Python is a dispatch bottleneck

However, many (most?) images should be processed into a consistent set of flavors:

- Size/resolution
- Format

What if, very early, we go ahead and do standard transformation, even if nothing asks for the image? What if the
transforms happened "in database", using a Rust SQLite extension function, tied directly to a trigger?

You might generate some images you didn't need. Perhaps a configuration system could help make statements to prevent
this.

The second improvement is the big one: caching. Many SSGs process the same unchanged images, over and over. It's
incredibly wasteful. If you have a database, which you trust, and a build process which extends this trust to the output
directories -- you likely can avoid most of the image rebuild.

# Database

Store all intermediate artifacts in a build "cache" implemented in schemaless SQLite.

## Background

Gatsby has a build cache with some interesting properties: extensible, GraphQL with extensible schemas, and a change
detection system. It became a very interesting engine to build an integration platform atop.

But it was very untrustworthy. When you have to frequently "blow the cache", you better have a fast system for full
builds. Which Gatsby didn't.

## Requirements

- *Trusted storage and retrieval*. Home-grown systems rarely become bulletproof, nor seen as bulletproof. (History on
  this: our pickle-based ZODB.)
- *Transactions*. In a related system, something with very strong transaction guarantees.
- *Fast and efficient*. Ultimately the system will store a LOT. It needs plenty of facilities for performing work
  without huge memory footprint.
- *Queries*. Rich facilities for finding the specific information needed.
- *Extensible*. Something everybody knows, but also provides escape-hatch extensibility if a computational roadblock
  arises.

## SQLite

With this in mind...imagine a build system designed around SQLite.

It's extremely trusted and ubiquitous. In fact, it's legendary in this regard. It obviously provides all the ideas of
transactional isolation, trusted storage retrieval, and the like.

From a speed perspective, when you move part of your model operations out of Python and into SQLite, those operations
will happen at C speed across multiple cores. In fact, SQLite allows multiple processes.

SQLite can work as a document database using JSON columns. These have rich query operations to look down into a
structure. Moreover, with indexing on computed columns, you can find "nodes" in your "corpus" in a high-performance way.
This also applies to updates with "patch" style updates.

One final option: extensions. If the database structure is a bottleneck, or if trips across the SQLite<->Python boundary
are a challenge, you can move operations "into the core." These can be in C, Rust, Go, etc.

## Status quo

Sphinx digests your corpus into a "doctree": a rich Python datastructure representing nodes and relations. But it treats
each document as a separate item. Its facilities for organizing a "corpus' are mostly "here's the array, go find what
you need." Also: only one type of build artifact is there: the neutral docutils parsed structure of the document.

Your templates? Jinja2 keeps a cache of parsed templates, but it is 100% independent of your "build system."
Configuration? It's all in a Python script. If it changes, it means rebuilding the universe. Images? External data?
You're on your own.

It's back to Gatsby, which also cobbled together a collection of designed-separately systems: Redux, a GraphQL library,
homegrown persistence.

## Vision

Imagine a stack written from to ground up atop a trusted system:

- Immutable store
- Computations stored in a neutral format
- Dependencies between calculations
- Registered handlers for changes
- Operations such as a template are "effects" triggered by a change
- These "effects" store their results and don't run if inputs don't change

This system would have a specific goal: 

- When the outside world's *inputs* change...
- what is the *least* amount of work, the shortest path...
- to update the outside world's outputs?

In this vision:

- The database is the source of truth
- Like Redux, the application flow goes through it and is dispatched by it
- Unlike Redux, it is persistent, transactional, and scalable
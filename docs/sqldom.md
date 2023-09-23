# SQLDOM

A big pile of "science fiction" describing how a fine-grained-change build system might be built around a SQL model.

# Simple Approach

Let's go through a bunch of scenarios with a very simple, naive version of the system.

We'll catalog some of the kinds of changes a SQLDOM system might see. For each change, we'll describe how the system
might react, along with implementation notes.

We'll start with the almost-nothing kind of change. Things will get very complicated, quickly, so we'll build things up
one step at a time.

## Startup, empty everything

You have a directory in `content`. It has no files in it.

You run a script. It generates a directory `build` with no files in it. But it also creates a sqlite file in a `var`
directory. This file has some tables. For now, it just has a `Sources` table.

## Full build, one input document

You have `content/a.txt` and no `build` directory. You run a build. It copies
the input document to `output/a.txt`.

The system scans the `content` directory and produces a batch of "changes":

```json
[
  {
    "path": "a.txt",
    "hash": "X3A234"
  }
]
```

After processing, the sources table now looks like this:

```json
[
  {
    "path": "a.txt",
    "hash": "X3A234",
    "content": "Hello World"
  }
]
```

The `build` directory:

```shell
$ ls build
a.txt
```

## Incremental, one unchanged input document

You have `content/a.txt` and no `build` directory. You run a build. It detects
that nothing has changed and the `build` directory is in sync. Thus, nothing
happens and a message is logged with the number of unchanged documents.

- Something needs to save some state between runs
- That's the `sources` table
- It has some mapping of paths to hashes
- The build discovers `a.txt`, hashes the contents, and checks the cache
- The cache knows about `a.txt` and says that it matches previous hash

When the run happens, the build system "diffs" the `content` directory and the `sources` table and determines these are
the changes:

```json
{}
```

Nothing changed. It's the same files on disk with the same hashes, as compared to the `sources` table.

The build system then needs to do a similar "diff" with the `build` directory. Thus, a `build` table:

```json
[
  {
    "path": "a.txt",
    "hash": "QZ234A",
    "content": "Hello"
  }
]
```

This table contains the final content as it should appear on disk -- currently, the same as the input. If the build
directory already has a file for that row, and the hash matches, nothing needs to be written.

Again, it's like rsync on the output. The authoritative final copy of ALL build artifacts are in the database. The
filesystem is just a mirror. If the filesystem copies get tampered with, the build system will notice.

## Change one input document

You have `content/a.txt` and `build/a.txt`. You also have database which knows the
hash from the last build -- for the inputs *and* the *outputs*.

You edit `content/a.txt` and change it, then run a build. It finds one file
at `content/a.txt`, takes the hash, and checks the cache. It's changed, so the
build copies the content to `build/a.txt` and updates the cache.

The changes:

```json
{
  "edits": [
    {
      "path": "a.txt",
      "hash": "QZ234A"
    }
  ]
}
```

The `sources` table now has:

```json
[
  {
    "path": "a.txt",
    "hash": "QZ234A",
    "content": "Hello World"
  }
]
```

And finally, the `build` table:

```json
[
  {
    "path": "a.txt",
    "hash": "QZ234A",
    "content": "Hello"
  }
]
```

## Server watch, one input document

You then run the build in watch mode. It starts up, scans `content`, checks the cache, and sees nothing has changed.
Same as before: a "diff" between the `content` directory and the `sources` table.

You change `content/a.txt`. The watcher sees a file has changed. It takes the
hash, checks the cache. Sees it is out of date. Updates the cache and copies to
output.

## Delete one input document

You delete `content/a.txt` and run the build. It collects all the paths under `content` and their hashes. The build then
does the "diff" against `sources` and determines the changeset:

```json
{
  "delete": [
    {
      "path": "a.txt",
    }
  ]
}
```

The `sources` table is now empty:

```json
[]
```

As is the `build` table:

```json
[]
```

Because the build table is empty, the `build/a.txt` needs to be deleted to match the `build` table. The "diff" does
this.

## Add one Markdown document with title

You add a file `content/b.md` as a valid Markdown file, with a title. You run the
build. It sees that `a.txt` hasn't changed, but there's a new path at `b.md`.

This time it runs two Python functions. `parse_markdown` extracts the `title` and
the `body`. `write_markdown` then puts a `title` and a `body` into a full HTML
document.

The build records the hash in the cache and writes the new HTML document
to `output/b.html`.

- Build phases

## Change parse function

You edit the `write_html` function and run the build. It sees that nothing has
changed in `input` and `build` and performs no work, thus skipping your change
to the HTML writer.

You change the build script to store your `build.py` file as a path in the
cache, with a hash. If your build script has changed, it triggers a full build.

## First dependency

An edit to anything in `build.py` triggers a full build. But why should `a.txt`
have to be rebuilt? It doesn't use the `write_html` function.

You change your build script to know that only `b.html` needs to be rebuilt
when the cache says `build.py` has changed.

## Link from b to a

You edit `b.html` to add `<a href="a.txt">Document A</a>`.

You run the build. It detects `content/b.html` has changed, runs the functions,
writes the output, and updates the cache.

## Link from a to b with title as link text

You make a policy that the first line of text files is the title. You then
write `parse_text` and `write_text` functions, similar to HTML. You change your
build script so that text files use these functions and do a build. You then
add `Document A` as the first-line title for `a.txt`.

You then change the system to allow `<a href="a.txt"></a>` to use the `title`
from the linked document. Meaning, if an `<a>` has no link text, ask the cache
for the `title` of that path, then insert it during `write_html`.

This means the cache now needs to store one more piece of info at a path: the
input hash, output hash, and the title.

You run the build and `output/b.html` has `<a href="a.txt">Document A</a>`.

## Change target title

You now edit `content/a.txt` and change the "title" (first line.) When you run
a build, the cache knows that `content/a.txt` has changed and updates.
But `build/b.html` does not have the new title.

You change the cache to track links between paths. The cache stores
that `b.html` points to the title on `a.txt`. If the `a.txt` `title`
changes, `b.html` gets rebuilt.

You do a "full build" (delete `var` and `output`) to get the information
stored. You then edit `content/a.txt` to change the title.

This time when you run the build, it updates `a.txt`. But it also triggers a
build on `b.html` via the link data.

## Target body changes but not title

You edit `content/a.txt` and change the body. When you run a build,
only `a.txt` gets rebuilt. `b.html` depended on the `title`, not the entire
document.

## Delete second doc

You delete `content/a.txt` and run a build. It sees the missing path and
removes `a.txt` from the cache and from `build/a.txt`.

Since `content/b.html` didn't change, the link data still thinks `b.html` links
to `title` in `a.txt`.
The build script looks at the link data, sees there's a missing path, and logs
an error.

## Remove link

You edit `content/b.html` and delete the `<a>` pointing to `a.txt`. You run the
script. The link entry gets removed and there is no error.

You put `content/a.txt` back, edit `content/b.html` to put back in the link,
and run the build. Everything is back to normal.

Notes:

- Database-driven
- Resources
- Build phases
- Dependencies
- Config files and changes
- Data cascade
- Images
- Themes
- Markdown sequences
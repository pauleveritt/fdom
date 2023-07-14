# Simple Approach

Let's go through a bunch of scenarios with a very simple, naive version of the system.
Even though it's naive, some parts (such as sync with build directory) are big improvement over current approaches.

Let's write a catalog of all the kinds of changes an fdom  system might see.
For each change, we'll describe how the system might react, along with
implementation notes.

We'll start with the almost-nothing kind of change.
Things will get very complicated, quickly, so we'll build things up one step at
a time.

## Startup, empty everything

You have a directory in `content`. It has no files in it.

You run a script. It generates a directory `build` with no files in it.

## Full build, one input document

You have `content/a.txt` and no `build` directory. You run a build. It copies
the input document to `output/a.txt`.

## Incremental, one input document

You have `content/a.txt` and no `build` directory. You run a build. It detects
that nothing has changed and the `build` directory is in sync. Thus, nothing
happens and a message is logged with the number of unchanged documents.

- Something needs to save some state between runs
- Let's say there's a `var` directory
- It has some mapping of paths to hashes
- The build discovers `a.txt`, hashes the contents, and checks the cache
- The cache knows about `a.txt` and says that it matches previous hash

## Change one input document

You have `content/a.txt` and `build/a.txt`. You also have `var` which knows the
hash from the last build.

You edit `content/a.txt` and change it, then run a build. It finds one file
at `content/a.txt`, takes the hash, and checks the cache. It's changed, so the
build copies the content to `build/a.txt` and updates the cache.

## Server watch, one input document

You then run the build in watch mode. It starts up, scans `content`, checks the
cache, and sees nothing has changed. Nothing gets copied.

You change `content/a.txt`. The watcher sees a file has changed. It takes the
hash, checks the cache. Sees it is out of date. Updates the cache and copies to
output.

- It is possible in the mode to skip the hash...you know it has changed
- But you'll need the hash anyway
- Thus, it is key to have a performant hash function

## Delete one input document

You delete `content/a.txt` and run the build. It collects all the paths
under `content` and their hashes. It then compares with the cache and sees that
there used to be something at `a.txt`.

The build deletes it from the cache and deletes it from `build/a.txt`.

## Modify built file

You edit `build/a.txt` and run the build. The correct version
of `build/a.txt` does not appear. You change the cache to track hashes
of `build`. Each path in the cache has input and output hashes.

You edit `content/a.txt` and run the build. It updates `output/a.txt` *and*
stores the hash of output file.

You again edit `build/a.txt` and run the build. This time it knows the output
is out-of-sync and copies the input to the output.

You run the build again. Nothing has changed in `content` or `build` so no
actions taken.

Instead of modifying `build/a.txt` you delete it. When you run the build, it
detects the missing path, then writes the file and stores the hash.

## Add one HTML document with title

You add a file `content/b.html` as a valid HTML file, with a title. You run the
build. It sees that `a.txt` hasn't changed, but there's a new path at `b.html`.

This time it runs two Python functions. `parse_html` extracts the `title` and
the `body`. `write_html` then puts a `title` and a `body` into a full HTML
document.

The build records the hash in the cache and writes the new HTML document
to `output/b.html`.

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


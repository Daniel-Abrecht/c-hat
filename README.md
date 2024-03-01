# C^ (C-Hat)

C^ is a programming language. It's basically C17, except with some small things changed or added.

It's just a quick proof of concept hack, and there are surely better & easier ways to do these things. The way it's
done, it nicely preserves all the spaces, though.

# Usage

This takes `file.c^` as input and outputs `file.c`.
```sh
./transpile file.c^ >file.c
```

# Features
## Array parameters

One thing has been added so far. If you have array arguments, you can have them before the arguments containing it's
dimensions. Things like this:
```c
void f(int x[n][m], int n, int m);
```

Things not yet implemented, which may be nice to have in the future:
* Syntax for Coroutines, Generators and Async functions
* Fixing `_Generic()`. It's annoying that it checks the semantics of non-matching branches.
* Reflection

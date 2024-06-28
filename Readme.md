# bwrap_devshell

This is a script that tarballs a
[numtide/devshell](https://github.com/numtide/devshell) and all of its
dependencies, and adds a script that drops users into this devshell with the
closure mounted in its expected location.

## How?

This script compresses a devshell's entire
[closure](https://zero-to-nix.com/concepts/closures), symlinks and all, to be
extracted with `tar -I zst -xPf ./out.tar.zst -C ./out`.

An included script, `./out/start`, drops the caller into the devshell inside a
[bubblewrap](https://github.com/containers/bubblewrap) environment where the
closure is mounted at `/nix`, making it fully usable, even without Nix itself
installed.

## Why?

In most cases, you should be using
[nix-portable](https://github.com/DavHau/nix-portable).

We encountered an exotic environment where systemd was not available
and we needed to share a massive installation of OpenLane 2 across many users.
From what we could tell, `nix-portable` requires the archive to be stored and
for each user to have a writable space for the archive. This allows the closure
to be shared by multiple users without the Nix daemon (or indeed a Nix
installation at all) available.


## License
Copyright 2024 Efabless Corporation. Available under the
[The Apache License, version 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt).

---

Incorporates code from [nix-portable](https://github.com/DavHau/nix-portable)

MIT License

Copyright (c) 2021 DavHau

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

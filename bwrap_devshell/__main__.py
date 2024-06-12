#!/usr/bin/env python3
# Copyright 2024 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Some code adapted from nix-portable
# Copyright (c) 2021 DavHau

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import pathlib
import tarfile
import textwrap
import tempfile
import functools
import subprocess
from typing import List

import click
import zstandard as zstd
from rich.progress import Progress


@click.command()
@click.argument("flake_target")
def main(flake_target):
    # Get derivation of devshell (must be numtide/devshell)
    devshell_store_path = subprocess.check_output(
        ["nix", "build", "--print-out-paths", "--no-link", flake_target],
        encoding="utf8",
    ).strip()

    # Verify it's a numtide devshell and get the path of the entry point
    bin_path = os.path.join(devshell_store_path, "bin", "devshell")
    if not os.path.isfile(bin_path):
        print("Not a valid devshell.")
        exit(os.EX_DATAERR)

    # Create Bubblewrap Script based on nix-portable
    start_script = textwrap.dedent(
        f"""
        #!/bin/bash
        export dir="$(dirname "$(readlink -f "$0")")"

        collectBinds(){{
            ### gather paths to bind for proot
            # we cannot bind / to / without running into a lot of trouble, therefore
            # we need to collect all top level directories and bind them inside an empty root
            pathsTopLevel="$(find / -mindepth 1 -maxdepth 1 -not -name nix -not -name dev)"


            toBind=""
            for p in $pathsTopLevel; do
                if [ -e "$p" ]; then
                real=$(realpath $p)
                if [ -e "$real" ]; then
                    if [[ "$real" == /nix/store/* ]]; then
                    storePath=$(storePathOfFile $real)
                    toBind="$toBind $storePath $storePath"
                    else
                    toBind="$toBind $real $p"
                    fi
                fi
                fi
            done


            # TODO: add /var/run/dbus/system_bus_socket
            paths="/etc/host.conf /etc/hosts /etc/hosts.equiv /etc/mtab /etc/netgroup /etc/networks /etc/passwd /etc/group /etc/nsswitch.conf /etc/resolv.conf /etc/localtime $HOME"

            for p in $paths; do
                if [ -e "$p" ]; then
                real=$(realpath $p)
                if [ -e "$real" ]; then
                    if [[ "$real" == /nix/store/* ]]; then
                    storePath=$(storePathOfFile $real)
                    toBind="$toBind $storePath $storePath"
                    else
                    toBind="$toBind $real $real"
                    fi
                fi
                fi
            done

            # if we're on a nixos, the /bin/sh symlink will point
            # to a /nix/store path which doesn't exit inside the wrapped env
            # we fix this by binding busybox/bin to /bin
            if test -s /bin/sh && [[ "$(realpath /bin/sh)" == /nix/store/* ]]; then
                toBind="$toBind $dir/busybox/bin /bin"
            fi
        }}


        makeBindArgs(){{
            arg=$1; shift
            sep=$1; shift
            binds=""
            while :; do
                if [ -n "$1" ]; then
                from="$1"; shift
                to="$1"; shift || {{ echo "no bind destination provided for $from!"; exit 3; }}
                binds="$binds $arg $from$sep$to";
                else
                break
                fi
            done
        }}
        
        collectBinds
        makeBindArgs --bind " " $toBind /etc/ssl /etc/ssl
        
        bwrap \\
            --bind $dir/empty / \\
            --dev-bind /dev /dev \\
            --bind $dir/nix /nix \\
            $binds \\
            {bin_path}
        """
    ).strip()

    # Gather every file and symlink
    closure_paths = (
        subprocess.check_output(
            ["nix-store", "--query", "--requisites", devshell_store_path],
            encoding="utf8",
        )
        .strip()
        .splitlines()
    )
    all_paths: List[pathlib.Path] = functools.reduce(
        lambda acc, elem: acc + list(pathlib.Path(elem).glob("**/*")), closure_paths, []
    )
    all_paths_filtered = [
        path for path in all_paths if path.is_symlink() or path.is_file()
    ]
    ## Put symlinks last, so their relative targets exist
    all_paths_sorted = sorted(
        all_paths_filtered,
        key=lambda x: 1 if x.is_symlink() else 0,
    )
    with tempfile.TemporaryDirectory() as d, Progress() as progress, zstd.open(
        "out.tar.zst", mode="wb"
    ) as stream, tarfile.TarFile(fileobj=stream, mode="w") as tf:
        ## Make writable (or else extraction will cry)
        def set_permissions(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
            tarinfo.mode = tarinfo.mode | 0o755
            return tarinfo

        task = progress.add_task(f"Compressing…", total=len(all_paths_sorted))
        for i, path in enumerate(all_paths_sorted):
            progress.update(task, completed=i + 1)
            print(f"Compressing '{path}'…")
            tf.add(path, arcname=str(path)[1:], filter=set_permissions)

        # Other files
        empty_dir = os.path.join(d, "empty")
        os.mkdir(empty_dir)
        tf.add(empty_dir, arcname="empty")
        start_script_path = os.path.join(d, "start")
        with open(start_script_path, "w", encoding="utf8") as f:
            f.write(start_script)
        os.chmod(start_script_path, 0o555)
        tf.add(start_script_path, arcname="start")
        progress.remove_task(task)


if __name__ == "__main__":
    main()

#!/usr/bin/python3

# CLI tool for managing encrypted vaults on Linux by
# the cryptsetup utility in a convenient manner.

import argparse
import hashlib
import itertools as it
import pathlib
import subprocess
import sys
import os


SIZE_SUF_MUL = {
    "": 1,
    "b": 1,

    "k": 10 ** 3,
    "m": 10 ** 6,
    "g": 10 ** 9,

    "kb": 10 ** 3,
    "mb": 10 ** 6,
    "gb": 10 ** 9,

    "kib": 2 ** 10,
    "mib": 2 ** 20,
    "gib": 2 ** 30
}


def calc_size(s):
    s = s.strip()
    suf = it.dropwhile(lambda x: x.isdigit(), s)
    suf = "".join(suf).lower()
    n = it.takewhile(lambda x: x.isdigit(), s)
    n = "".join(n)

    if len(suf) + len(n) != len(s) or SIZE_SUF_MUL.get(suf) is None:
        raise ValueError

    return int(n) * SIZE_SUF_MUL[suf]


def perr(*args, **kwargs):
    print("\x1b[1;31mERROR:\x1b[0m\a", *args, file=sys.stderr, **kwargs)
    sys.exit(1)


def run_cmd(args: list[str]):
    args = list(map(str, args))
    res = subprocess.run(args)
    if res.returncode:
        perr(f"Shell command failed: {args}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=[
                        "mount", "unmount", "create", "destroy"])
    parser.add_argument("--size", "-s")
    parser.add_argument("--path", "-p")
    parser.add_argument("vaultfile")
    args = parser.parse_args()

    vaultfile = pathlib.Path(args.vaultfile)
    label = "vault-" + \
        hashlib.sha256(str(vaultfile.resolve()).encode("utf-8")).hexdigest()
    # Do not resolve if mapper is just a symlink
    mapdev = pathlib.Path(f"/dev/mapper/{label}")
    mounted_at = None

    # Get mount point if mapdev already mounted
    with open("/proc/mounts") as f:
        for l in f:
            fields = l.strip().split()
            if fields and fields[0] == str(mapdev):
                mounted_at = fields[1]

    if os.getuid() != 0:
        perr(f"{parser.prog} should be run as superuser (use sudo)")

    if args.operation == "mount":
        if args.path is None:
            perr("--path/-p is missing!")
        if not vaultfile.is_file():
            perr(f"'{vaultfile}' does not exists or not a file")
        if mounted_at:
            perr(
                f"Expected mapper '{mapdev}' already mounted at '{mounted_at}'")
        if mapdev.is_block_device():
            perr(
                f"'{vaultfile}' is already opened at expected '{mapdev}', close it manually.")

        path = pathlib.Path(args.path)
        if not path.exists():
            print(f"Mount path '{path}', does not exist, creating new...")
            path.mkdir(parents=True)

        if not path.is_dir():
            perr(f"'{path}' is not a directory!")
        if path.is_mount():
            perr(f"'{path}' is already a mount path")
        if list(path.glob("*")):
            perr("Directory not empty!")

        print("Opening vault...")
        run_cmd(["cryptsetup", "open", vaultfile, label, "--type=luks"])

        print("Mounting vault...")
        run_cmd(["mount", "-t", "ext4", mapdev, path])
        print(f"Mounted at: '{path}'")

    elif args.operation == "unmount":
        if not vaultfile.is_file():
            perr(f"'{vaultfile}' does not exists or is not a file")
        if not mapdev.is_block_device():
            perr(f"'{vaultfile}' not opened at expected '{mapdev}'")
        if not mounted_at:
            perr(f"'{vaultfile}' not mounted")

        print("Unmounting...")
        run_cmd(["umount", mounted_at])

        print("Closing vault...")
        run_cmd(["cryptsetup", "close", label])

        print("Removing mount-point...")
        run_cmd(["rmdir", mounted_at])

    elif args.operation == "create":
        if args.size is None:
            perr("--size/-s is missing!")

        if vaultfile.exists():
            perr(f"'{vaultfile}' already exists!")
        if mapdev.exists():
            perr(f"'{mapdev}' already exists")

        try:
            size = calc_size(args.size)
        except ValueError:
            perr(f"Invalid size given!")
        # As header is 16MiB, so 16MiB is for header only
        if size < 32_000_000:
            perr("Size must be at least 32MB (32_000_000 bytes)")

        print(f"Creating vault image(size= {size:,} Bytes)...")
        run_cmd(["fallocate", "-l", size, vaultfile])

        print(f"Formatting as LUKS...")
        run_cmd(["cryptsetup", "--verify-passphrase", "luksFormat", vaultfile])

        print("Formatting as ext4...\n Enter passphrase again")
        run_cmd(["cryptsetup", "open", vaultfile, label, "--type=luks"])
        run_cmd(["mkfs.ext4", "-L", label[:15], mapdev])
        run_cmd(["cryptsetup", "close", label])

    elif args.operation == "destroy":
        if not vaultfile.is_file():
            perr(f"'{vaultfile}' does not exist or is not a file")

        if mapdev.exists():
            print(f"Vault is open at '{mapdev}', closing...")
            run_cmd(["cryptsetup", "close", label])

        yes = input("Are you sure?[type YES then]: ") == "YES"
        if not yes:
            perr("User aborted.")
        print("Removing file...")
        run_cmd(["rm", vaultfile])


if __name__ == "__main__":
    main()
    print("\x1b[1mDone.\x1b[0m\a")  # Print in bold

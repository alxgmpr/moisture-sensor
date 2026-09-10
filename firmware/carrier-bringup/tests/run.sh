#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
${CC:-cc} -std=c11 -Wall -Wextra -Werror ${CFLAGS:-} -o "$out/test" "$here/test_carrier.c" "$here/../src/carrier.c"
"$out/test"

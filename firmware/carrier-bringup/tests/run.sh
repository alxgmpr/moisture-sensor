#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
${CC:-cc} -std=c11 -Wall -Wextra -Werror ${CFLAGS:-} -o "$out/test" \
    "$here/test_carrier.c" "$here/../src/carrier.c"
"$out/test"
${CC:-cc} -std=c11 -Wall -Wextra -Werror ${CFLAGS:-} -I"$here/../src" \
    -o "$out/test_bthome" "$here/test_bthome.c" "$here/../src/bthome.c"
"$out/test_bthome"
python3 "$here/validate_versions.py"
if [ -n "${DFU_PACKAGE:-}" ]; then
    python3 "$here/validate_dfu.py" "$DFU_PACKAGE"
fi

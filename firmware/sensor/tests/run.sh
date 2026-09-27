#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
${CC:-cc} -std=c11 -Wall -Wextra -Werror ${CFLAGS:-} -o "$out/test" \
    "$here/test_sensor.c" "$here/../src/sensor.c"
"$out/test"
${CC:-cc} -std=c11 -Wall -Wextra -Werror ${CFLAGS:-} -I"$here/../src" \
    -o "$out/test_bthome" "$here/test_bthome.c" "$here/../src/bthome.c"
"$out/test_bthome"
${CC:-cc} -std=c11 -Wall -Wextra -Werror ${CFLAGS:-} -I"$here/../src" \
    -o "$out/test_config" "$here/test_config.c" "$here/../src/config.c"
"$out/test_config"
CONFIG_TEST_BIN="$out/test_config" node --test "$here/../dashboard/protocol.test.mjs"
python3 "$here/validate_versions.py"
python3 "$here/validate_partitions.py"
if [ -n "${FIRMWARE_PARTITIONS:-}" ]; then
    python3 "$here/validate_partitions.py" "$FIRMWARE_PARTITIONS"
fi
if [ -n "${DFU_PACKAGE:-}" ]; then
    python3 "$here/validate_dfu.py" "$DFU_PACKAGE"
fi

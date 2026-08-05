#!/bin/sh
# Host test runner. No container and no Zephyr: bthome.c is pure C.
set -e

here=$(dirname "$0")
out=$(mktemp -d)/test_bthome

cc -std=c11 -Wall -Wextra -Werror -o "$out" \
	"$here/test_bthome.c" "$here/../../src/bthome.c"

"$out"

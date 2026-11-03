#!/bin/bash
# shellcheck disable=SC2034
unused_but_disabled=1
greet() {
  local msg=$(printf '%s' "$1")
  echo $msg
  return
}
arr=(a b c)
echo "${arr}"
rm -rf "$PREFIX/"*
greet "$@"

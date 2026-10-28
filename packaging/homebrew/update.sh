#!/bin/sh
# Sets packaging/homebrew/vu.rb to a release: its version and the sha256 of its macOS archive.
#   packaging/homebrew/update.sh 0.3.0
v="$1"; [ -n "$v" ] || { echo "usage: update.sh VERSION"; exit 2; }
f="$(dirname "$0")/vu.rb"
sum=$(gh release download "v$v" -R vu0tran/vu -p SHA256SUMS -O - | grep "vu-$v-macos-arm64.tar.gz" | cut -d' ' -f1)
[ -n "$sum" ] || { echo "no macOS archive in release v$v"; exit 1; }
sed -i.bak -e "s/^  version \".*\"/  version \"$v\"/" -e "s/^  sha256 \".*\"/  sha256 \"$sum\"/" "$f" && rm -f "$f.bak"
echo "vu.rb: $v $sum"

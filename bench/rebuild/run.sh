#!/bin/bash
# Build and rebuild times, Vu against Rust, on gen.py's program of N functions in M modules:
# a clean build, then a one-line edit in the middle module and the rebuild, for the error check
# (vu check, cargo check), the edit-and-run loop (vu run, cargo run), the build for a debugger
# (vu build --debug, cargo build) and the optimized one (vu build, cargo build --release). Each
# time is the median of 3. The C compiler is the one vu picks (CC unset); a clean build starts with
# no kept parts (split builds) and no target folder (cargo).
#   bench/rebuild/run.sh N M
set -e
here="$(cd "$(dirname "$0")" && pwd)"
VU=${VU:-"$here/../../vu"}
n=${1:-2000}; m=${2:-20}
w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
python3 "$here/gen.py" "$n" "$m" "$w"
unset VU_CACHE CC
export VU_RUN_CACHE=off XDG_CACHE_HOME="$w/cache"   # (where split builds keep their parts)
mid=$((m / 2))
edit() {  # change one constant in one function of the middle module, a new value each time
  sed -i "s/^  var t = x + [0-9]*$/  var t = x + $RANDOM/;T;:a;n;ba" "$w/vu/m$mid.vu"
  sed -i "s/^    let mut t = x + [0-9]*;$/    let mut t = x + $RANDOM;/;T;:a;n;ba" "$w/rs/src/m$mid.rs"
}
t() { local s=$(date +%s.%N); "$@" >/dev/null 2>&1 || { echo "failed: $*" >&2; exit 1; }; echo "$(date +%s.%N) - $s" | bc; }
med() { printf '%s\n' "$@" | sort -n | sed -n 2p; }
lines() { cat "$@" | wc -l; }
echo "$(cc --version | head -1); $(clang --version 2>/dev/null | head -1); $(rustc --version); $(nproc) cores"
echo "program: $n functions in $m modules; Vu $(lines "$w"/vu/*.vu) lines, Rust $(lines "$w"/rs/src/*.rs) lines"
row() {  # name, clean command (vu), clean (rust), rebuild (vu), rebuild (rust)
  local a=() b=() c=() d=()
  for i in 1 2 3; do
    rm -rf "$w/rs/target" "$w/prog" "$w/cache"
    a+=($(t bash -c "$2")); b+=($(cd "$w/rs" && t bash -c "$3"))
    edit
    c+=($(t bash -c "$4")); d+=($(cd "$w/rs" && t bash -c "$5"))
  done
  printf '%-28s  clean: Vu %6.2f s  Rust %6.2f s   after an edit: Vu %6.2f s  Rust %6.2f s\n' "$1" "$(med "${a[@]}")" "$(med "${b[@]}")" "$(med "${c[@]}")" "$(med "${d[@]}")"
}
row "check (errors only)" "$VU check $w/vu/main.vu" "cargo check -q" "$VU check $w/vu/main.vu" "cargo check -q"
row "run (quick build)" "$VU run $w/vu/main.vu" "cargo run -q" "$VU run $w/vu/main.vu" "cargo run -q"
row "build for a debugger" "$VU build --debug $w/vu/main.vu -o $w/prog" "cargo build -q" "$VU build --debug $w/vu/main.vu -o $w/prog" "cargo build -q"
row "optimized build" "$VU build $w/vu/main.vu -o $w/prog" "cargo build -q --release" "$VU build $w/vu/main.vu -o $w/prog" "cargo build -q --release"

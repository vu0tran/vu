#!/bin/sh
# Writes a Homebrew formula for a vgolint release, from the release's SHA256SUMS:
#   packaging/homebrew/vgolint_formula.sh 0.1.0 SHA256SUMS > vgolint.rb
# release-tools.yml attaches it to the vgolint release as a file; it isn't committed or published.
# To serve it from this repository's tap, copy it to Formula/vgolint.rb on main:
#   brew tap vu0tran/vu https://github.com/vu0tran/vu && brew install vu0tran/vu/vgolint
set -eu
v="${1#vgolint-}"; v="${v#v}"; sums="$2"
sum() {
  s=$(awk -v f="vgolint-$v-$1.tar.gz" '$2 == f || $2 == "*" f { print $1 }' "$sums")
  [ -n "$s" ] || { echo "vgolint_formula.sh: no vgolint-$v-$1.tar.gz in $sums" >&2; exit 1; }
  echo "$s"
}
ma=$(sum darwin-arm64); mx=$(sum darwin-amd64); lx=$(sum linux-amd64); la=$(sum linux-arm64)
base="https://github.com/vu0tran/vu/releases/download/vgolint-v$v"
cat <<RB
# Homebrew formula for vgolint, written by packaging/homebrew/vgolint_formula.sh.
# vgolint reads the Go standard library and the module cache as golangci-lint does: it needs Go.
# It doesn't install a golangci-lint command (that would clash with Homebrew's golangci-lint);
# alias it in your shell or Makefile, or use install.sh, which does.
class Vgolint < Formula
  desc "Drop-in replacement for golangci-lint run, written in Vu"
  homepage "https://github.com/vu0tran/vu/tree/main/golint"
  license "MIT"
  version "$v"

  depends_on "go"

  on_macos do
    on_arm do
      url "$base/vgolint-$v-darwin-arm64.tar.gz"
      sha256 "$ma"
    end
    on_intel do
      url "$base/vgolint-$v-darwin-amd64.tar.gz"
      sha256 "$mx"
    end
  end

  on_linux do
    on_intel do
      url "$base/vgolint-$v-linux-amd64.tar.gz"
      sha256 "$lx"
    end
    on_arm do
      url "$base/vgolint-$v-linux-arm64.tar.gz"
      sha256 "$la"
    end
  end

  def install
    bin.install "vgolint"
  end

  test do
    assert_match "built with vgolint", shell_output("#{bin}/vgolint version")
    (testpath/"go.mod").write "module example.com/t\n\ngo 1.22\n"
    (testpath/"main.go").write "package main\n\nimport \"os\"\n\nfunc main() {\n\tos.Remove(\"x\")\n}\n"
    output = shell_output("#{bin}/vgolint run --no-cache 2>&1", 1)
    assert_match "Error return value of \`os.Remove\` is not checked (errcheck)", output
  end
end
RB

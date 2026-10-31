#!/bin/sh
# Writes the Homebrew formula for a release, from the release's SHA256SUMS:
#   packaging/homebrew/formula.sh 0.3.0 SHA256SUMS > Formula/vu.rb
# The release workflow runs it and commits Formula/vu.rb to main, so this repository is the tap:
#   brew tap vu0tran/vu https://github.com/vu0tran/vu && brew install vu0tran/vu/vu
set -eu
v="${1#v}"; sums="$2"
sum() {
  s=$(awk -v f="vu-$v-$1.tar.gz" '$2 == f || $2 == "*" f { print $1 }' "$sums")
  [ -n "$s" ] || { echo "formula.sh: no vu-$v-$1.tar.gz in $sums" >&2; exit 1; }
  echo "$s"
}
mac=$(sum macos-arm64); lx=$(sum linux-x64); la=$(sum linux-arm64)
base="https://github.com/vu0tran/vu/releases/download/v$v"
cat <<RB
# Homebrew formula for Vu, written by packaging/homebrew/formula.sh for each release.
#   brew tap vu0tran/vu https://github.com/vu0tran/vu && brew install vu0tran/vu/vu
# Vu builds programs through a C compiler (on macOS, the Command Line Tools'); libomp is for par
# loops and OpenSSL for TLS.
class Vu < Formula
  desc "Compiled, memory-safe language with Python-style syntax that compiles to C"
  homepage "https://vulang.org"
  version "$v"

  on_macos do
    depends_on arch: :arm64
    depends_on "libomp"
    depends_on "openssl@3"
    url "$base/vu-$v-macos-arm64.tar.gz"
    sha256 "$mac"
  end

  on_linux do
    depends_on "openssl@3"
    on_intel do
      url "$base/vu-$v-linux-x64.tar.gz"
      sha256 "$lx"
    end
    on_arm do
      url "$base/vu-$v-linux-arm64.tar.gz"
      sha256 "$la"
    end
  end

  def install
    libexec.install Dir["*"]
    # a script, not a link: vuc finds std/ next to its own folder
    (bin/"vu").write <<~SH
      #!/bin/sh
      exec "#{libexec}/compiler/vuc" "\$@"
    SH
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/vu version")
    (testpath/"hello.vu").write "fn main():\\n  print(\\"hello\\")\\n"
    assert_equal "hello\\n", shell_output("#{bin}/vu run #{testpath}/hello.vu")
  end
end
RB

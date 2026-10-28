# Homebrew formula for Vu, for a tap (github.com/vu0tran/homebrew-vu: `brew install vu0tran/vu/vu`).
# Each release: set version, and the sha256 of vu-<version>-macos-arm64.tar.gz from the release's
# SHA256SUMS (packaging/homebrew/update.sh does both). It needs a C compiler at run time (Vu builds
# through it), which macOS has with the Command Line Tools; OpenSSL and libomp are for TLS programs
# and par loops.
class Vu < Formula
  desc "Compiled, memory-safe language with Python-style syntax that compiles to C"
  homepage "https://vulang.org"
  version "0.2.0"
  url "https://github.com/vu0tran/vu/releases/download/v#{version}/vu-#{version}-macos-arm64.tar.gz"
  sha256 "REPLACE_WITH_SHA256"
  depends_on arch: :arm64
  depends_on "libomp"
  depends_on "openssl@3"

  def install
    libexec.install Dir["*"]
    (bin/"vu").write <<~SH
      #!/bin/sh
      exec "#{libexec}/compiler/vuc" "$@"
    SH
  end

  test do
    (testpath/"hello.vu").write "fn main():\n  print(\"hello\")\n"
    assert_equal "hello\n", shell_output("#{bin}/vu run #{testpath}/hello.vu")
  end
end

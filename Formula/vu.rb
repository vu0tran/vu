# Homebrew formula for Vu, written by packaging/homebrew/formula.sh for each release.
#   brew tap vu0tran/vu https://github.com/vu0tran/vu && brew install vu0tran/vu/vu
# Vu builds programs through a C compiler (on macOS, the Command Line Tools'); libomp is for par
# loops and OpenSSL for TLS.
class Vu < Formula
  desc "Compiled, memory-safe language with Python-style syntax that compiles to C"
  homepage "https://vulang.org"
  version "0.3.0"

  on_macos do
    depends_on arch: :arm64
    depends_on "libomp"
    depends_on "openssl@3"
    url "https://github.com/vu0tran/vu/releases/download/v0.3.0/vu-0.3.0-macos-arm64.tar.gz"
    sha256 "3a419836e9737925f47b4bd4d4f6cf518e1a8fb5752246df1db133a6cec9dc06"
  end

  on_linux do
    depends_on "openssl@3"
    on_intel do
      url "https://github.com/vu0tran/vu/releases/download/v0.3.0/vu-0.3.0-linux-x64.tar.gz"
      sha256 "8140376430596e8ce7de1268388d422f96046f7831548c54ea8ba75eabf75baf"
    end
    on_arm do
      url "https://github.com/vu0tran/vu/releases/download/v0.3.0/vu-0.3.0-linux-arm64.tar.gz"
      sha256 "8b000e024dbbb9dab3969c35029403264af934fa73538d3f90f3e4756fda2355"
    end
  end

  def install
    libexec.install Dir["*"]
    # a script, not a link: vuc finds std/ next to its own folder
    (bin/"vu").write <<~SH
      #!/bin/sh
      exec "#{libexec}/compiler/vuc" "$@"
    SH
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/vu version")
    (testpath/"hello.vu").write "fn main():\n  print(\"hello\")\n"
    assert_equal "hello\n", shell_output("#{bin}/vu run #{testpath}/hello.vu")
  end
end

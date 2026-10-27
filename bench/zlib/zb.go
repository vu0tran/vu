// zlib-format decompression with Go's compress/zlib, N times: zb FILE.z N.
package main

import (
	"bytes"
	"compress/zlib"
	"fmt"
	"hash/crc32"
	"io"
	"os"
	"strconv"
)

func main() {
	in, _ := os.ReadFile(os.Args[1])
	n, _ := strconv.Atoi(os.Args[2])
	var out []byte
	for k := 0; k < n; k++ {
		r, err := zlib.NewReader(bytes.NewReader(in))
		if err != nil {
			panic(err)
		}
		out, err = io.ReadAll(r)
		if err != nil {
			panic(err)
		}
	}
	fmt.Println(len(out), crc32.ChecksumIEEE(out))
}

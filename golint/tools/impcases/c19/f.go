package c19

import (
	"os" // c-os
	"fmt" // c-fmt
	"strings" // c-strings
	"sort" // c-sort
	"errors" // c-errors
	"io" // c-io
	"bytes" // c-bytes
	"time" // c-time
	"net/http" // c-http
	"encoding/json" // c-json
	"imp.test/m/lib/a" // c-a
	"imp.test/m/lib/b" // c-b
	"imp.test/m/loc/c" // c-c
	"imp.test/m/loc/d" // c-d
)

func init() {
	_ = os.Args
	fmt.Println()
	_ = strings.ToUpper
	_ = sort.Ints
	_ = errors.New
	_ = io.EOF
	_ = bytes.NewBuffer
	_ = time.Now
	_ = http.Get
	_ = json.Marshal
	_ = a.A
	_ = b.B
	_ = c.C
	_ = d.D
}

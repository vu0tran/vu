package c32

import (
	"os"
	"fmt" // a
	"strings"
	"sort" // b
	"errors"
	"io"
	"bytes" // c
	"time"
	"net/http"
	"encoding/json"
	_ "embed" // dup
	"math"
	_ "embed" // dup
	"unicode"
	_ "embed" // dup
	"path"
	_ "embed"
	_ "unsafe" // u
	_ "unsafe" // u
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
	_ = math.Abs
	_ = unicode.IsLetter
	_ = path.Base
}

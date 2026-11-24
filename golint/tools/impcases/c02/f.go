package c02

import (
	"imp.test/m/lib/b"
	"fmt"
	"imp.test/m/loc/c"
	"os"
	"imp.test/m/lib/a"
)

func init() {
	_ = b.B
	fmt.Println()
	_ = c.C
	_ = os.Args
	_ = a.A
}

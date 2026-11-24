package c27

import (
	"imp.test/m/loc/c"
	"imp.test/m/lib/a"
)

import (
	"fmt"
	"os"
)

func init() {
	_ = c.C
	_ = a.A
	fmt.Println()
	_ = os.Args
}

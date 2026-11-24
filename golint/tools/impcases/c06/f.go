package c06

import (
	"imp.test/m/loc/c"

	"fmt"
	"imp.test/m/lib/a"

	"os"
)

func init() {
	_ = c.C
	fmt.Println()
	_ = a.A
	_ = os.Args
}

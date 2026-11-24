package c04

import "fmt"
import "os"
import (
	"imp.test/m/lib/a"
	"strings"
)

func init() {
	fmt.Println()
	_ = os.Args
	_ = a.A
	_ = strings.ToUpper
}

package c20

import "fmt"

import (
	"os"
)

// doc of strings import
import "strings"

func init() {
	fmt.Println()
	_ = os.Args
	_ = strings.ToUpper
}

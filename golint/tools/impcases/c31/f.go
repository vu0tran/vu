package c31

// #include <stdlib.h>
import "C"

import "os"
import (
	"fmt"
	"strings"
)

func init() {
	_ = os.Args
	fmt.Println()
	_ = strings.ToUpper
	C.free(nil)
}

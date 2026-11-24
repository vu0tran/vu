package c09

import (
	"imp.test/m/lib/go-thing"
	"imp.test/m/lib/x/v3"
	"imp.test/m/lib/util.v1"
	"imp.test/m/lib/v2"
	"fmt"
)

func init() {
	_ = thing.T
	_ = x.X
	_ = util.U
	_ = vtwo.V
	fmt.Println()
}

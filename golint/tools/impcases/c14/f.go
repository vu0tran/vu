package c14

import (
	// leading comment
	"os"

	// group two
	"fmt"
	"bytes"
)

func init() {
	_ = os.Args
	fmt.Println()
	_ = bytes.NewBuffer
}

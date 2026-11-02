// The release smoke test's module: a finding from each of a few linters, standard library only.
package main

import (
	"fmt"
	"os"

	"example.com/smoke/pkg"
)

func main() {
	x := 1
	x = 2
	x = 3
	os.Remove("tmp")
	fmt.Println(pkg.Double(int(3)), x)
}

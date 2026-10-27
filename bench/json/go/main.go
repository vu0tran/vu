// Parse a JSON file into a generic tree (interface{}) with the standard library and count nodes.
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func count(v interface{}, n *[6]int) {
	switch x := v.(type) {
	case nil:
		n[0]++
	case bool:
		n[1]++
	case float64:
		n[2]++
	case string:
		n[3]++
	case []interface{}:
		n[4]++
		for _, e := range x {
			count(e, n)
		}
	case map[string]interface{}:
		n[5]++
		for _, e := range x {
			count(e, n)
		}
	}
}

func main() {
	src, _ := os.ReadFile(os.Args[1])
	var v interface{}
	if err := json.Unmarshal(src, &v); err != nil {
		panic(err)
	}
	var n [6]int
	count(v, &n)
	fmt.Printf("objects %d, arrays %d, strings %d, numbers %d\n", n[5], n[4], n[3], n[2])
}

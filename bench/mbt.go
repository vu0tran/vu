package main

import (
	"crypto/md5"
	"fmt"
	"os"
	"runtime"
	"strconv"
	"sync"
)

func inside(cr, ci float64) bool {
	var zr, zi, tr, ti float64
	for b := 0; b < 10; b++ {
		for k := 0; k < 5; k++ {
			zi = (zr+zr)*zi + ci
			zr = tr - ti + cr
			tr = zr * zr
			ti = zi * zi
		}
		if tr+ti > 4.0 {
			return false
		}
	}
	return true
}

func main() {
	n := 200
	if len(os.Args) > 1 {
		n, _ = strconv.Atoi(os.Args[1])
	}
	size := (n + 7) / 8 * 8
	row := size / 8
	inv := 2.0 / float64(size)
	fmt.Printf("P4\n%d %d\n", size, size)
	px := make([]byte, size*row)
	threads := runtime.NumCPU()
	var wg sync.WaitGroup
	for t := 0; t < threads; t++ {
		wg.Add(1)
		go func(t int) {
			defer wg.Done()
			for y := t; y < size; y += threads {
				ci := float64(y)*inv - 1.0
				for x := 0; x < row; x++ {
					var b byte
					for bit := 0; bit < 8; bit++ {
						if inside(float64(x*8+bit)*inv-1.5, ci) {
							b |= 0x80 >> bit
						}
					}
					px[y*row+x] = b
				}
			}
		}(t)
	}
	wg.Wait()
	fmt.Printf("%x\n", md5.Sum(px))
}

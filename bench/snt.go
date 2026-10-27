package main

import (
	"fmt"
	"math"
	"os"
	"runtime"
	"strconv"
	"sync"
)

func a(i, j int) float64 { return 1.0 / float64((i+j)*(i+j+1)/2+i+1) }

func mul(v, out []float64, transpose bool) {
	threads := runtime.NumCPU()
	var wg sync.WaitGroup
	for t := 0; t < threads; t++ {
		wg.Add(1)
		go func(t int) {
			defer wg.Done()
			for i := t; i < len(out); i += threads {
				sum := 0.0
				for j, vj := range v {
					if transpose {
						sum += a(j, i) * vj
					} else {
						sum += a(i, j) * vj
					}
				}
				out[i] = sum
			}
		}(t)
	}
	wg.Wait()
}

func main() {
	n := 100
	if len(os.Args) > 1 {
		n, _ = strconv.Atoi(os.Args[1])
	}
	u, v, tmp := make([]float64, n), make([]float64, n), make([]float64, n)
	for i := range u {
		u[i] = 1
	}
	for i := 0; i < 10; i++ {
		mul(u, tmp, false)
		mul(tmp, v, true)
		mul(v, tmp, false)
		mul(tmp, u, true)
	}
	var vbv, vv float64
	for i := range v {
		vbv += u[i] * v[i]
		vv += v[i] * v[i]
	}
	fmt.Printf("%0.9f\n", math.Sqrt(vbv/vv))
}

package main

import (
	"fmt"
	"os"
	"strconv"
)

func main() {
	n := 7
	if len(os.Args) > 1 {
		n, _ = strconv.Atoi(os.Args[1])
	}
	perm, perm1, count := make([]int, n), make([]int, n), make([]int, n)
	for i := range perm1 {
		perm1[i] = i
	}
	maxFlips, checksum, permCount, r := 0, 0, 0, n
	for {
		for ; r != 1; r-- {
			count[r-1] = r
		}
		copy(perm, perm1)
		flips := 0
		for k := perm[0]; k != 0; k = perm[0] {
			for lo, hi := 0, k; lo < hi; lo, hi = lo+1, hi-1 {
				perm[lo], perm[hi] = perm[hi], perm[lo]
			}
			flips++
		}
		if flips > maxFlips {
			maxFlips = flips
		}
		if permCount%2 == 0 {
			checksum += flips
		} else {
			checksum -= flips
		}
		for {
			if r == n {
				fmt.Printf("%d\nPfannkuchen(%d) = %d\n", checksum, n, maxFlips)
				return
			}
			first := perm1[0]
			copy(perm1[:r], perm1[1:r+1])
			perm1[r] = first
			count[r]--
			if count[r] > 0 {
				break
			}
			r++
		}
		permCount++
	}
}

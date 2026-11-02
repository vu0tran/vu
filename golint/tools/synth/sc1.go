package synth

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"
	"time"
)

func demorgan(a, b bool, x, y int) {
	if !(a && b) {
		fmt.Println()
	}
	if !(x == 1 || y == 2) {
		fmt.Println()
	}
	if !(x < 1) {
		fmt.Println()
	}
	if !a || !b {
		fmt.Println()
	}
}

func tagged(x int, s string) {
	if x == 1 {
		fmt.Println(1)
	} else if x == 2 {
		fmt.Println(2)
	} else if x == 3 {
		fmt.Println(3)
	}
	if x == 1 {
		fmt.Println(1)
	} else if x == 2 || x == 4 {
		fmt.Println(2)
	} else {
		fmt.Println(0)
	}
	if x == 1 {
		fmt.Println(1)
	}
	switch {
	case s == "a":
		fmt.Println()
	case s == "b", s == "c":
		fmt.Println()
	}
	switch {
	case x == 1:
	case s == "b":
	}
}

func replaces(s string, b []byte) {
	_ = strings.Replace(s, "a", "b", -1)
	_ = bytes.Replace(b, []byte("a"), []byte("b"), -1)
	_ = strings.Replace(s, "a", "b", 2)
	_ = strings.SplitN(s, ",", -1)
}

func lift(xs []int) {
	i := 0
	for {
		if i >= len(xs) {
			break
		}
		i++
	}
	for {
		if i < 0 {
			break
		}
		fmt.Println(i)
		i--
	}
}

func wsprintf(b *bytes.Buffer, sb *strings.Builder, n int) {
	b.WriteString(fmt.Sprintf("%d", n))
	sb.WriteString(fmt.Sprintf("%d", n))
	b.Write([]byte(fmt.Sprintf("%d", n)))
}

func blanks(ch chan int, m map[string]int) {
	x, _ := <-ch
	_ = x
	for k, _ := range m {
		_ = k
	}
	for _ = range m {
	}
	for _, _ = range m {
	}
}

func contains(s string, b []byte) bool {
	if strings.Index(s, "x") != -1 {
		return true
	}
	if strings.Index(s, "y") == -1 {
		return false
	}
	if strings.IndexAny(s, "y") >= 0 {
		return false
	}
	if bytes.Index(b, []byte("z")) < 0 {
		return false
	}
	return strings.IndexRune(s, 'r') > -1
}

func nilLen(m map[string]int, s []int) bool {
	if m != nil && len(m) > 0 {
		return true
	}
	if s == nil || len(s) == 0 {
		return true
	}
	return false
}

func slices2(s []int, str string) {
	_ = s[1:len(s)]
	_ = str[2:len(str)]
	_ = s[:len(s)]
}

func since(t time.Time) time.Duration {
	return time.Now().Sub(t)
}

func makes(n int) {
	_ = make([]int, n, n)
	_ = make([]int, 0, n)
	_ = make(map[int]int, 0)
	_ = make(chan int, 0)
}

func merge() int {
	var x int
	x = 5
	var y string
	y = "a"
	return x + len(y)
}

func redundant(x int) {
	switch x {
	case 1:
		fmt.Println()
		break
	}
	return
}

func sprintfStr(s string) string {
	return fmt.Sprintf("%s", s)
}

func sprintfStr2(err error) string {
	return fmt.Sprintf("%s", err)
}

func deferClose() error {
	f, err := os.Open("x")
	defer f.Close()
	if err != nil {
		return err
	}
	return nil
}

type item struct{ a, b int }

func pool(p *sync.Pool) {
	p.Put(item{})
	p.Put(&item{})
	p.Put([]byte{})
	p.Put("s")
	p.Put(1)
}

func ws(w io.Writer, b []byte) {
	io.WriteString(w, string(b))
}

func emptyBranch(x int) {
	if x > 0 {
	}
	if x > 1 {
		// nothing
	} else {
	}
}

var ErrBad = errors.New("bad")
var errGood = errors.New("good")
var badName = errors.New("bad name")
var BadName2 = fmt.Errorf("bad name")

func errStrings() error {
	if true {
		return errors.New("Something failed")
	}
	if false {
		return fmt.Errorf("Failed: %d", 1)
	}
	return errors.New("ok.")
}

type Self struct{}

func (self Self) A()  {}
func (this *Self) B() {}
func (s Self) C()     {}

func errorLast() (error, int) { return nil, 0 }

func durations() {
	var timeoutSec time.Duration
	var waitMs time.Duration = time.Millisecond
	_ = timeoutSec
	_ = waitMs
}

func yoda(x int) bool {
	if 5 == x {
		return true
	}
	return "a" == "b"
}

func omitType() {
	var x int = 5
	var s *Self = &Self{}
	var y fmt.Stringer = nil
	_ = x
	_ = s
	_ = y
}

func strconvTo(x []byte) string {
	return fmt.Sprintf("%s", string(x))
}

func forSelect(ch chan int) {
	for {
		select {
		case v := <-ch:
			fmt.Println(v)
		}
	}
}

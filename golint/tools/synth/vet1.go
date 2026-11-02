package synth

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type point struct{ x, y int }

type T struct {
	A int    `json:"a"`
	B string `json:"b,omitempty"`
	C string `json:"a"`
	D int    `xml:"d" json:"d"`
	E int    `json:d`
	F int    `json:"f" json:"g"`
	G int    `bad tag`
	H int    `json:",omitempty"`
	I int    `json:"-"`
	J int    `json:"-,"`
	k int    `json:"k"`
	L int    "json:\"l\""
	M int    `xml:"m,attr"`
	N int    `xml:"m,attr"`
	O int    `  json:"o"`
	P int    `json:"p" `
}

func assigns() {
	x := 1
	x = x
	var p point
	p.x = p.x
	s := []int{1}
	s[0] = s[0]
	fmt.Println(x, p, s)
}

func bools(a, b int, f func() bool) {
	if a == 1 || a == 1 {
		fmt.Println()
	}
	if a != 1 || a != 2 {
		fmt.Println()
	}
	if a == 1 && a == 2 {
		fmt.Println()
	}
	if f() || f() {
		fmt.Println()
	}
	if a > b && a > b {
		fmt.Println()
	}
}

func printfs(n int, s string, e error) {
	fmt.Printf("%d\n", s)
	fmt.Printf("%s %s\n", s)
	fmt.Printf("%d\n", n, n)
	fmt.Println("x %d", n)
	fmt.Printf("%z\n", n)
	fmt.Sprintf("%v", n)
	fmt.Printf("%s\n", n)
	fmt.Printf("%x %X %o %b %c %q %U\n", n, n, n, n, n, n, n)
	fmt.Printf("%f\n", s)
	fmt.Printf("%t\n", n)
	fmt.Printf("%p\n", n)
	fmt.Errorf("err %d", s)
	fmt.Fprintf(os.Stderr, "%d %s\n", n)
	fmt.Printf("%*d\n", n, n)
	fmt.Printf("%[2]d %[1]s\n", s, n)
	fmt.Printf("%[3]d\n", n)
	fmt.Printf("%v %w\n", n, e)
	fmt.Println("hello\n")
	fmt.Printf("%.2f %6.2f %-5d %+d %05d\n", 1.0, 2.0, n, n, n)
	fmt.Printf("%s\n", e)
	fmt.Printf("%d%%\n", n)
	fmt.Printf("%")
	fmt.Print("a", "b\n")
	fmt.Println(s, "%s")
	var b strings.Builder
	fmt.Fprintln(&b, "x\n")
	_ = strconv.Itoa(n)
}

func unreachableCode() int {
	return 1
	fmt.Println("never")
	return 2
}

func unreachable2(x int) int {
	for {
		if x > 0 {
			return x
		}
	}
	return 0
}

func unreachable3() {
	panic("x")
	fmt.Println()
}

func results(s string) {
	errors.New("x")
	fmt.Sprintf("%s", s)
	fmt.Sprint(s)
	strings.TrimSpace(s)
	_ = strings.Replace(s, "a", "b", -1)
	strings.Replace(s, "a", "b", 1)
	bytesHelper([]byte(s))
}

func bytesHelper(b []byte) []byte { return b }

type myReader struct{}

func (myReader) ReadByte() (int, error) { return 0, nil }
func (myReader) WriteTo(w io.Writer) error { return nil }
func (myReader) Seek(off int64, whence int) int64 { return 0 }
func (myReader) String() string { return "" }
func (myReader) MarshalJSON() ([]byte, error) { return nil, nil }

func locks() {
	var mu sync.Mutex
	m2 := mu
	_ = m2
	f := func(m sync.Mutex) {}
	f(mu)
}

func shifts() {
	var b int8 = 1
	_ = b << 9
	var u uint16 = 1
	_ = u >> 16
	_ = u << 15
}

func conv(i int, r rune, b byte) {
	_ = string(i)
	_ = string(r)
	_ = string(b)
}

func nilfuncs() {
	if assigns == nil {
		fmt.Println()
	}
	if nil != bools {
		fmt.Println()
	}
}

func resp() {
	res, err := http.Get("http://x")
	defer res.Body.Close()
	if err != nil {
		return
	}
}

func timeFmt(t time.Time) string {
	return t.Format("2006-02-01")
}

func sleepy() {
	time.Sleep(1)
	time.Sleep(10)
	time.Sleep(time.Second)
}

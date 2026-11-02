package synth

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"math/rand"
	"os"
	"sync"
)

type Locked struct {
	mu sync.Mutex
	n  int
}

type Wrap struct {
	l Locked
}

type Arr [2]sync.Mutex

type RW struct{ sync.RWMutex }

type noCopy struct{}

func (*noCopy) Lock()   {}
func (*noCopy) Unlock() {}

type NC struct {
	_ noCopy
	x int
}

type Pt struct{ X, Y float64 }
type Ip struct{ X, Y int }

type MyBytes []byte

func (MyBytes) String() string { return "" }

type B byte

func cl1(l Locked) int { return l.n }

func (w Wrap) cl2() int { return 0 }

func cl3(ls []Locked) {
	for _, l := range ls {
		_ = l.n
	}
	for i := range ls {
		_ = i
	}
	var a Arr
	b := a
	_ = b
	var w Wrap
	var w2 = w
	_ = w2
	x := []Wrap{w}
	_ = x
	m := map[string]Locked{"a": {}}
	_ = m
	nc := NC{}
	nc2 := nc
	_ = nc2
	var rw RW
	rw2 := rw
	_ = rw2
	p := &w
	w3 := *p
	_ = w3
	f := func(r RW) {}
	f(rw)
	_ = new(Locked)
	_ = fmt.Sprint(len(ls))
}

func cl4(w *Wrap) Wrap {
	return *w
}

func cl5() (Locked, error) {
	var l Locked
	return l, nil
}

func cl6(wg sync.WaitGroup, o sync.Once, c *sync.Cond) {
	var c2 = *c
	_ = c2
}

func sa4000(a, b int, f float64, p Pt, q Ip, s string, xs []int) bool {
	if a == a || b != b {
		return true
	}
	_ = f == f
	_ = p == p
	_ = q == q
	_ = a - a
	_ = a + a
	_ = s < s
	_ = xs[0] == xs[0]
	_ = rand.Intn(2) - rand.Intn(2)
	_ = len(s) == len(s)
	_ = (a) == (a)
	_ = a&a == 0
	_ = 1 == 1
	return a > a && b >= b
}

type Tags struct {
	A int `json:"a,omitempty,omitempty"`
	B int `json:"b,bogus"`
	C int `json:"c,string"`
	D []int `json:"d,string"`
	E *int `json:"e,string"`
	F int `json:"f;g"`
	G int `xml:"g,attr,attr"`
	H int `xml:"h,foo"`
	I int `yaml:"i" yaml:"j"`
	J int `json:"j,omitzero,inline"`
	K int `json:"k,format:x,y"`
	L int `json:"-,"`
	M int `xml:",chardata"`
	N int `json:"n" xml:"n,any,any,comment,comment"`
}

func qf1010(b []byte, mb MyBytes, bb []B, w io.Writer, l *log.Logger, buf *bytes.Buffer) {
	fmt.Println(b)
	fmt.Print("x", b, 1)
	fmt.Println(mb)
	fmt.Println(bb)
	_ = fmt.Sprint(b)
	_ = fmt.Sprintln(b)
	fmt.Fprintln(os.Stdout, b)
	fmt.Fprint(w, b)
	fmt.Printf("%s", b)
	log.Println(b)
	l.Print(b)
	io.WriteString(w, string(b))
	io.WriteString(w, string(bb))
	io.WriteString(buf, string(b[1:]))
	args := []interface{}{b}
	fmt.Println(args...)
}

func qf1007(c bool, d int) bool {
	x := false
	if c {
		x = true
	}
	y := true
	if d > 3 {
		y = false
	}
	z := true
	if c {
		z = true
	}
	w := false
	if c {
		w = true
	} else {
		w = false
	}
	v := false
	if c {
		v = true
		d++
	}
	u := false
	if q := d; q > 0 {
		u = true
	}
	g := func() bool {
		t := false
		if c {
			t = true
		}
		return t
	}
	return x || y || z || w || v || u || g()
}

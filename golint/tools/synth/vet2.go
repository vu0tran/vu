package synth

import (
	"encoding/json"
	"encoding/xml"
	"errors"
	"image"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"sync/atomic"
	"time"
	"unicode"
)

type MyErr struct{}

func (MyErr) Error() string { return "" }

type local struct{ a, b int }

func Vet2(xs []int, n int32, p *int64, b []byte) {
	xs = append(xs)
	_ = append(xs, 1)
	n = atomic.AddInt32(&n, 1)
	*p = atomic.AddInt64(p, 1)
	m := atomic.AddInt32(&n, 1)
	_ = m
	start := time.Now()
	defer println(time.Since(start))
	defer func() { println(time.Since(start)) }()
	var err error
	var me MyErr
	var pme *MyErr
	var s string
	var e2 interface{}
	_ = errors.As(err, &err)
	_ = errors.As(err, me)
	_ = errors.As(err, &me)
	_ = errors.As(err, &pme)
	_ = errors.As(err, &s)
	_ = errors.As(err, e2)
	_ = errors.As(err, nil)
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt)
	c2 := make(chan os.Signal, 1)
	signal.Notify(c2)
	signal.Notify(make(chan os.Signal))
	var v struct{ A int }
	_ = json.Unmarshal(b, v)
	_ = json.Unmarshal(b, &v)
	_ = xml.Unmarshal(b, v)
	_ = json.NewDecoder(nil).Decode(v)
	_ = json.NewDecoder(nil).Decode(&v)
	_ = url.Userinfo{}
	_ = url.URL{"http", "", nil, "", "", "", false, false, "", "", ""}
	_ = &url.URL{Scheme: "x"}
	_ = image.Point{1, 2}
	_ = unicode.Range16{1, 2, 3}
	_ = local{1, 2}
	_ = []url.Values{{"a": nil}}
	_ = []*url.URL{{"http", "", nil, "", "", "", false, false, "", "", ""}}
	_ = struct{ A, B int }{1, 2}
}

func Vet2b(cl *http.Client, cv http.Client) error {
	resp, err := http.Get("x")
	defer resp.Body.Close()
	if err != nil {
		return err
	}
	r2, err := cl.Get("y")
	defer r2.Body.Close()
	r3, err := cv.Head("y")
	defer r3.Body.Close()
	r4, err := http.Get("x")
	if err != nil {
		return err
	}
	defer r4.Body.Close()
	return err
}

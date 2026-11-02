package synth

import (
	"testing"
	"time"
)

func TestGoroutine(t *testing.T) {
	go func() {
		t.Fatal("x")
	}()
	go func() {
		t.FailNow()
	}()
	go func() {
		t.Error("ok")
	}()
	time.Sleep(time.Millisecond)
}

func Testbad(t *testing.T) {}

func BenchmarkX(b *testing.B) {}

func ExampleNothing() {}

func TestWrongSig(x int) {}

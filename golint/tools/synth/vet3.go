package synth

import (
	"encoding/xml"
	"fmt"
	"io"
)

type SM struct{}

func (SM) MarshalJSON() string                 { return "" }
func (SM) UnmarshalJSON(b []byte) (err error)  { return nil }
func (*SM) ReadByte() byte                     { return 0 }
func (SM) WriteTo(w io.Writer) (n int64)       { return 0 }
func (SM) WriteTo2(w io.Writer) (n int64)      { return 0 }
func (SM) Seek(off int64, whence int) int64    { return 0 }
func (SM) Format(f fmt.State, c int)           {}
func (SM) Scan(s fmt.ScanState, verb rune) int { return 0 }
func (SM) GobDecode(b ...byte) error           { return nil }
func (SM) ReadFrom(r io.Reader) (int, error)   { return 0, nil }
func (SM) UnmarshalXML(d *xml.Decoder, s xml.StartElement) bool {
	return false
}
func (SM) ReadRune() (r rune, size int, err error) { return 0, 0, nil }
func (SM) UnreadRune(x int) error                  { return nil }
func (SM) Error() string                           { return "" }
func (SM) Unwrap() SM                              { return SM{} }
func (SM) Is(target SM) bool                       { return false }
func (SM) As(target any) bool                      { return false }

type NE struct{}

func (NE) Unwrap() int { return 0 }

type SI interface {
	MarshalJSON() ([]byte, string)
	GobEncode() []byte
	WriteByte(b byte) error
	UnreadByte() (error, int)
}

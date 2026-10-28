use std::io::{self, Read, Write};

#[derive(Clone, Copy, PartialEq, Debug)]
enum Tok {
    Num(i128),
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
}

fn tokenize(s: &[u8]) -> Option<Vec<Tok>> {
    let mut toks = Vec::new();
    let mut i = 0;
    while i < s.len() {
        let c = s[i];
        match c {
            b' ' => {
                i += 1;
            }
            b'0'..=b'9' => {
                let mut v: i128 = 0;
                while i < s.len() && s[i].is_ascii_digit() {
                    v = v.checked_mul(10)?.checked_add((s[i] - b'0') as i128)?;
                    i += 1;
                }
                toks.push(Tok::Num(v));
            }
            b'+' => {
                toks.push(Tok::Plus);
                i += 1;
            }
            b'-' => {
                toks.push(Tok::Minus);
                i += 1;
            }
            b'*' => {
                toks.push(Tok::Star);
                i += 1;
            }
            b'/' => {
                toks.push(Tok::Slash);
                i += 1;
            }
            b'(' => {
                toks.push(Tok::LParen);
                i += 1;
            }
            b')' => {
                toks.push(Tok::RParen);
                i += 1;
            }
            _ => return None,
        }
    }
    Some(toks)
}

struct Parser {
    toks: Vec<Tok>,
    pos: usize,
}

impl Parser {
    fn peek(&self) -> Option<Tok> {
        self.toks.get(self.pos).copied()
    }

    fn expr(&mut self) -> Option<i128> {
        let mut v = self.term()?;
        loop {
            match self.peek() {
                Some(Tok::Plus) => {
                    self.pos += 1;
                    let r = self.term()?;
                    v = v.checked_add(r)?;
                }
                Some(Tok::Minus) => {
                    self.pos += 1;
                    let r = self.term()?;
                    v = v.checked_sub(r)?;
                }
                _ => return Some(v),
            }
        }
    }

    fn term(&mut self) -> Option<i128> {
        let mut v = self.unary()?;
        loop {
            match self.peek() {
                Some(Tok::Star) => {
                    self.pos += 1;
                    let r = self.unary()?;
                    v = v.checked_mul(r)?;
                }
                Some(Tok::Slash) => {
                    self.pos += 1;
                    let r = self.unary()?;
                    if r == 0 {
                        return None;
                    }
                    v = v.checked_div(r)?;
                }
                _ => return Some(v),
            }
        }
    }

    fn unary(&mut self) -> Option<i128> {
        if self.peek() == Some(Tok::Minus) {
            self.pos += 1;
            let v = self.unary()?;
            return v.checked_neg();
        }
        self.primary()
    }

    fn primary(&mut self) -> Option<i128> {
        match self.peek()? {
            Tok::Num(n) => {
                self.pos += 1;
                Some(n)
            }
            Tok::LParen => {
                self.pos += 1;
                let v = self.expr()?;
                if self.peek() != Some(Tok::RParen) {
                    return None;
                }
                self.pos += 1;
                Some(v)
            }
            _ => None,
        }
    }
}

fn evaluate(line: &[u8]) -> Option<i64> {
    let toks = tokenize(line)?;
    let mut p = Parser { toks, pos: 0 };
    let v = p.expr()?;
    if p.pos != p.toks.len() {
        return None;
    }
    i64::try_from(v).ok()
}

fn main() {
    let mut data = Vec::new();
    io::stdin().read_to_end(&mut data).unwrap();

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for raw in data.split(|&b| b == b'\n') {
        let line = raw.strip_suffix(b"\r").unwrap_or(raw);
        if line.is_empty() {
            continue;
        }
        match evaluate(line) {
            Some(v) => writeln!(out, "{}", v).unwrap(),
            None => writeln!(out, "error").unwrap(),
        }
    }
}

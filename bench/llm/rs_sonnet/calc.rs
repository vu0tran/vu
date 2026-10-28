use std::io::{self, Read, Write};

struct Parser<'a> {
    s: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    fn skip_ws(&mut self) {
        while self.pos < self.s.len() && self.s[self.pos] == b' ' {
            self.pos += 1;
        }
    }

    fn peek(&mut self) -> Option<u8> {
        self.skip_ws();
        self.s.get(self.pos).copied()
    }

    fn expr(&mut self) -> Result<i128, ()> {
        let mut v = self.term()?;
        loop {
            match self.peek() {
                Some(b'+') => {
                    self.pos += 1;
                    let r = self.term()?;
                    v = v.checked_add(r).ok_or(())?;
                }
                Some(b'-') => {
                    self.pos += 1;
                    let r = self.term()?;
                    v = v.checked_sub(r).ok_or(())?;
                }
                _ => return Ok(v),
            }
        }
    }

    fn term(&mut self) -> Result<i128, ()> {
        let mut v = self.unary()?;
        loop {
            match self.peek() {
                Some(b'*') => {
                    self.pos += 1;
                    let r = self.unary()?;
                    v = v.checked_mul(r).ok_or(())?;
                }
                Some(b'/') => {
                    self.pos += 1;
                    let r = self.unary()?;
                    if r == 0 {
                        return Err(());
                    }
                    v = v.checked_div(r).ok_or(())?;
                }
                _ => return Ok(v),
            }
        }
    }

    fn unary(&mut self) -> Result<i128, ()> {
        match self.peek() {
            Some(b'-') => {
                self.pos += 1;
                let v = self.unary()?;
                v.checked_neg().ok_or(())
            }
            _ => self.primary(),
        }
    }

    fn primary(&mut self) -> Result<i128, ()> {
        match self.peek() {
            Some(b'(') => {
                self.pos += 1;
                let v = self.expr()?;
                if self.peek() == Some(b')') {
                    self.pos += 1;
                    Ok(v)
                } else {
                    Err(())
                }
            }
            Some(c) if c.is_ascii_digit() => {
                let mut v: i128 = 0;
                while self.pos < self.s.len() && self.s[self.pos].is_ascii_digit() {
                    v = v
                        .checked_mul(10)
                        .and_then(|x| x.checked_add((self.s[self.pos] - b'0') as i128))
                        .ok_or(())?;
                    self.pos += 1;
                }
                Ok(v)
            }
            _ => Err(()),
        }
    }
}

fn eval(line: &[u8]) -> Option<i128> {
    let mut p = Parser { s: line, pos: 0 };
    let v = p.expr().ok()?;
    if p.peek().is_some() {
        return None;
    }
    Some(v)
}

fn main() {
    let mut data = Vec::new();
    io::stdin().read_to_end(&mut data).unwrap();
    let mut lines: Vec<&[u8]> = data.split(|&b| b == b'\n').collect();
    if let Some(last) = lines.last() {
        if last.is_empty() {
            lines.pop();
        }
    }
    let out = io::stdout();
    let mut out = out.lock();
    for mut line in lines {
        if line.last() == Some(&b'\r') {
            line = &line[..line.len() - 1];
        }
        if line.is_empty() {
            continue;
        }
        match eval(line) {
            Some(v) => writeln!(out, "{}", v).unwrap(),
            None => writeln!(out, "error").unwrap(),
        }
    }
}

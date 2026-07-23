"""Minimal LZF-compatible compressor/decompressor.

Implements the classic liblzf stream format:
  - control byte < 32:  literal run of (control + 1) bytes follows
  - control byte >= 32: back-reference
        length_field = control >> 5           (0..7)
        if length_field == 7: length = 7 + next_byte + 2   (extra length byte)
        else:                 length = length_field + 2
        offset = ((control & 0x1f) << 8) + next_byte + 1   (1..8192, back from current output position)

This is the format used inside Crush Crush's save files (see README).
"""

MAX_LITERAL = 32
MAX_OFF = 1 << 13  # 8192
MAX_REF_SHORT = 8  # length_field 0..6 => length 2..8 without an extra byte
MAX_REF = 264      # length_field 7 + extra byte(0..255) + 2


def decompress(buf):
    i = 0
    n = len(buf)
    out = bytearray()
    while i < n:
        ctrl = buf[i]
        i += 1
        if ctrl < 32:
            length = ctrl + 1
            out += buf[i:i + length]
            i += length
        else:
            length = ctrl >> 5
            if length == 7:
                length += buf[i]
                i += 1
            length += 2
            ref = len(out) - ((ctrl & 0x1f) << 8) - 1 - buf[i]
            i += 1
            if ref < 0:
                raise ValueError("corrupt LZF stream: back-reference before start of output")
            for _ in range(length):
                out.append(out[ref])
                ref += 1
    return bytes(out)


def compress(data):
    """Greedy LZ77 encoder that emits a valid LZF stream (not byte-identical to
    any particular reference encoder, but always decodes back to `data`)."""
    n = len(data)
    out = bytearray()
    htab = {}  # 3-byte key -> list of positions (most recent last)

    def key(pos):
        return bytes(data[pos:pos + 3])

    i = 0
    lit_start = 0

    def flush_literals(end):
        nonlocal out
        pos = lit_start
        while pos < end:
            chunk = min(MAX_LITERAL, end - pos)
            out.append(chunk - 1)
            out += data[pos:pos + chunk]
            pos += chunk

    while i < n:
        best_len = 0
        best_off = 0
        if i + 3 <= n:
            k = key(i)
            candidates = htab.get(k)
            if candidates:
                for cand in reversed(candidates):
                    off = i - cand
                    if off > MAX_OFF:
                        break
                    max_len = min(MAX_REF, n - i)
                    l = 0
                    while l < max_len and data[cand + l] == data[i + l]:
                        l += 1
                    if l > best_len:
                        best_len = l
                        best_off = off
                        if l >= MAX_REF:
                            break

        if best_len >= 3:
            flush_literals(i)
            length = best_len - 2
            if length < 7:
                ctrl = (length << 5) | ((best_off - 1) >> 8)
                out.append(ctrl)
                out.append((best_off - 1) & 0xff)
            else:
                extra = length - 7
                ctrl = (7 << 5) | ((best_off - 1) >> 8)
                out.append(ctrl)
                out.append(extra)
                out.append((best_off - 1) & 0xff)

            for p in range(i, i + best_len):
                if p + 3 <= n:
                    htab.setdefault(key(p), []).append(p)
            i += best_len
            lit_start = i
        else:
            if i + 3 <= n:
                htab.setdefault(key(i), []).append(i)
            i += 1

    flush_literals(n)
    return bytes(out)

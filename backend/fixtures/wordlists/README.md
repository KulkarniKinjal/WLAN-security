# Wordlists

Drop a plain-text wordlist (one candidate passphrase per line) here to
make it selectable in the Wireless Lab's WPA/WPA2 scenario.

A small sample list is provided (`sample-small.txt`) for quick testing
against a capture whose real passphrase you've deliberately set to one
of these values in your own authorized lab setup -- it is **not** a
real-world cracking list and will not find real-world passwords.

For a larger, well-known list, Kali ships `rockyou.txt` compressed at:

```
/usr/share/wordlists/rockyou.txt.gz
```

Decompress it and copy (or symlink) it into this directory:

```bash
sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz
cp /usr/share/wordlists/rockyou.txt ./backend/fixtures/wordlists/
```

Only use it against captures you are authorized to test.

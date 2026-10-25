# Capture fixtures

This project does not bundle any .pcap/.pcapng/.cap files, since a
usable WEP or WPA capture requires an authorized network you control.

To create your own authorized test captures:

- **WEP:** set up a WEP-secured AP in your own isolated lab (many
  routers still support legacy WEP mode for exactly this kind of
  teaching exercise) and capture traffic with `airodump-ng` while
  generating some traffic.
- **WPA/WPA2:** set up a WPA2-Personal AP in your own lab with a
  passphrase from your wordlist, then capture the 4-way handshake
  with `airodump-ng` while a client (re)connects -- you can force a
  reconnect on a client you own, but do not run deauthentication
  against any network/client you do not own or control.

Upload the resulting file through the Wireless Lab page. The
Environment Doctor and the upload endpoint will tell you if a file
can't be parsed or is missing required metadata.

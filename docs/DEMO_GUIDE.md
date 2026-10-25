# Examiner Demonstration Guide

A ~10-minute walkthrough covering all three modules plus a fallback if
a live tool/VM isn't available at demo time.

## 0. Before you start

- Start the backend and frontend (see `docs/WINDOWS_SETUP.md` step 17, or `scripts/start-dev.sh`).
- Open the Dashboard. Point out the **mode badge** (DEMO or REAL) in the sidebar — explain this is never silent.
- Open **Environment Doctor** and walk through the checks. Explain that a Warning ≠ broken — it just means that specific tool falls back to demonstration mode.

## 1. Wireless module (2–3 min)

- Go to **Wireless Lab**.
- Select the WPA/WPA2 dictionary scenario.
- Upload an authorized sample capture (a `.pcap` with a captured 4-way handshake you are authorized to test — see the wordlist/capture note in the README).
- Select the bundled wordlist, start the experiment.
- Narrate while it runs: "This never fabricates a result — if the tool isn't installed, or the capture has no usable handshake, it will say so rather than pretend to succeed."
- Show the **Evidence panel**: objective / what it proves / what it does NOT prove / defense.

**Fallback:** if `aircrack-ng`/`tshark` aren't installed on the demo machine, the same flow runs in demonstration mode automatically — the result is clearly labeled "DEMONSTRATION FIXTURE" throughout the UI and PDF.

## 2. Metasploit module (2–3 min)

- Go to **Metasploit Lab**.
- Show the single fixed scenario description (vsftpd 2.3.4 backdoor) and explain the safety gates out loud: target must be configured, inside the isolated host-only CIDR, and reachable — otherwise it refuses to run.
- Run it against the configured Metasploitable2 target.
- Point out the evidence distinguishes "process ran" from "backdoor actually confirmed" (port 6200 / session observed).

**Fallback:** if the VM isn't running, the Doctor page will already show this, and the experiment will cleanly report `evidence_invalid` with the exact reason (e.g. "FTP service not reachable") rather than hanging or faking success.

## 3. Awareness simulator (2 min)

- Go to **Awareness Simulator**, pick any of the three scenarios.
- Deliberately pick the "wrong"/less-safe option once to show the debrief calling it out, with the red flag explained and the safer choice shown.
- Emphasize: fictional branding, no real network, no real or dummy credentials stored — only decisions and the score.

## 4. History, comparison, and reporting (2 min)

- Go to **Session History**.
- Use the search/module filter.
- Check two compatible sessions (e.g. two wireless runs) to show the side-by-side comparison view.
- Open a session, download the PDF report, open it to show the mode banner and limitations section.
- Delete a session to show the confirmation step.

## If something breaks live

- Any adapter failure surfaces as a labeled `evidence_invalid`/`failed` session with a plain-language reason — show that instead of a crash, and explain that's by design (section 13 of the project spec: "never claim success you can't verify").
- If the whole backend is unreachable, fall back to walking through a previously exported PDF/JSON report and the architecture diagram in `README.md`.

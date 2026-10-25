"""
Experiment registry: the single, fixed list of lab scenarios the app will
ever run. Nothing outside this list is executable -- there is no
arbitrary-command endpoint anywhere in the backend. Adding a scenario
means editing this file and its adapter, not something the UI can do.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Module = Literal["wireless_wep", "wireless_wpa", "metasploit", "awareness"]


@dataclass(frozen=True)
class Scenario:
    id: str
    module: Module
    title: str
    objective: str
    description: str
    requires_wordlist: bool = False
    defense: str = ""


SCENARIOS: dict[str, Scenario] = {
    "wep_key_recovery_demo": Scenario(
        id="wep_key_recovery_demo",
        module="wireless_wep",
        title="WEP key recovery (authorized offline capture)",
        objective=(
            "Show that WEP's RC4 key-scheduling weakness lets an attacker recover the "
            "network key from a sufficiently large set of captured IVs, using aircrack-ng "
            "against a pre-recorded, authorized capture file."
        ),
        description=(
            "Requires an uploaded .cap/.pcap containing WEP-encrypted data frames with "
            "enough unique initialization vectors. The app runs aircrack-ng in a fixed, "
            "non-interactive mode against the capture only -- it never transmits anything."
        ),
        defense="Do not use WEP. Use WPA2/WPA3-Personal or WPA2/3-Enterprise with a strong passphrase/certificates.",
    ),
    "wpa_dictionary_test": Scenario(
        id="wpa_dictionary_test",
        module="wireless_wpa",
        title="WPA/WPA2-Personal bounded dictionary test",
        objective=(
            "Show that a weak WPA/WPA2-Personal passphrase can be recovered offline from a "
            "captured 4-way handshake using a dictionary attack, and that a passphrase "
            "absent from the wordlist is correctly reported as 'not found', not 'secure'."
        ),
        description=(
            "Requires an uploaded capture containing a complete authorized WPA/WPA2 4-way "
            "handshake (EAPOL) for the target BSSID, plus a fixed supplied wordlist. Runs "
            "aircrack-ng in dictionary mode. WPA3 (SAE) captures are rejected -- this attack "
            "does not apply to WPA3."
        ),
        requires_wordlist=True,
        defense="Use a long, random passphrase (15+ characters) or WPA3-Personal (SAE), which resists offline dictionary attacks.",
    ),
    "vsftpd_234_backdoor": Scenario(
        id="vsftpd_234_backdoor",
        module="metasploit",
        title="vsftpd 2.3.4 backdoor (Metasploitable2 lab target)",
        objective=(
            "Demonstrate CVE-2011-2523: vsftpd 2.3.4 contains a backdoor triggered by a "
            "':)' smiley in the FTP USER field, which opens a listener on TCP 6200. This "
            "experiment connects to confirm the listener, rather than spawning an "
            "interactive shell in the UI."
        ),
        description=(
            "Runs `exploit/unix/ftp/vsftpd_234_backdoor` via msfconsole in resource-script "
            "mode against the single configured lab target, then verifies success by "
            "confirming port 6200 opened and closes the session immediately. Restricted to "
            "a target inside the host-only lab network (configured CIDR)."
        ),
        defense="Patch vsftpd to a maintained version; this backdoored build should never be exposed, including on isolated lab networks for longer than the exercise.",
    ),
}


def get_scenario(scenario_id: str) -> Scenario | None:
    return SCENARIOS.get(scenario_id)


def scenarios_for(module: Module) -> list[Scenario]:
    return [s for s in SCENARIOS.values() if s.module == module]

"""
Fictional captive-portal social-engineering simulator.

Entirely self-contained and client-driven: the frontend renders invented
portal branding and the
backend only ever receives the student's multiple-choice decisions. No
free-text password field exists in the UI; a "dummy credentials" button
submits a fixed literal string so nothing resembling a real password is
ever collected or stored.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AwarenessStep:
    id: str
    prompt: str
    red_flag: str  # what a careful user should notice
    options: tuple[str, ...]
    safe_option: str


@dataclass(frozen=True)
class AwarenessScenario:
    id: str
    title: str
    brand: str
    narrative: str
    steps: tuple[AwarenessStep, ...]


SCENARIOS: dict[str, AwarenessScenario] = {
    "oversharing_portal": AwarenessScenario(
        id="oversharing_portal",
        title="The 'Free Airport Wi-Fi' that wants everything",
        brand="CloudHarbor Guest Wi-Fi (fictional)",
        narrative=(
            "You're at a café. A network called 'CloudHarbor Guest Wi-Fi' shows a captive portal "
            "asking for your full name, date of birth, and phone number before granting access."
        ),
        steps=(
            AwarenessStep(
                id="step1",
                prompt="The portal asks for your date of birth and phone number just to get internet access. Do you proceed or leave?",
                red_flag="A guest Wi-Fi network has no legitimate need for your date of birth or phone number.",
                options=("Proceed and fill in real info", "Proceed using obviously fake dummy info", "Leave and don't connect"),
                safe_option="Leave and don't connect",
            ),
            AwarenessStep(
                id="step2",
                prompt="The portal address uses an unfamiliar domain and has no clear venue contact. What do you do?",
                red_flag="A mismatched domain and missing operator contact make the page difficult to verify.",
                options=("Continue because the page looks polished", "Ask venue staff to confirm the portal", "Enter the requested details quickly"),
                safe_option="Ask venue staff to confirm the portal",
            ),
        ),
    ),
    "urgency_threat_portal": AwarenessScenario(
        id="urgency_threat_portal",
        title="'Your session will be suspended' portal",
        brand="Northstar Guest Access (fictional)",
        narrative=(
            "A portal named 'Northstar Guest Access' displays a red banner: 'URGENT: Verify your identity "
            "within 2 minutes or your access will be permanently suspended.'"
        ),
        steps=(
            AwarenessStep(
                id="step1",
                prompt="A countdown timer pressures you to act fast and 'verify your identity'. What do you do?",
                red_flag="Urgency and threats are classic pressure tactics used to short-circuit careful thinking.",
                options=("Rush to verify before the timer ends", "Ignore the timer and inspect the page first", "Close the tab immediately without looking"),
                safe_option="Ignore the timer and inspect the page first",
            ),
            AwarenessStep(
                id="step2",
                prompt="The page asks you to install an unknown browser extension to continue. What do you do?",
                red_flag="Unexpected software installation is not necessary for ordinary guest Wi-Fi access.",
                options=("Install it to avoid losing access", "Close the page and use another connection", "Disable browser warnings and continue"),
                safe_option="Close the page and use another connection",
            ),
        ),
    ),
    "inconsistent_identity_portal": AwarenessScenario(
        id="inconsistent_identity_portal",
        title="The portal with mismatched branding",
        brand="\"Pinebeam_Guest\" network, portal titled \"CedarLink\" (fictional, deliberately inconsistent)",
        narrative=(
            "You join a network called 'Pinebeam_Guest', but the captive "
            "portal that loads is titled 'CedarLink' with a different logo and color scheme."
        ),
        steps=(
            AwarenessStep(
                id="step1",
                prompt="The network name, portal branding, and hotel name all disagree with each other. What do you do?",
                red_flag="Inconsistent names/branding between the Wi-Fi network and its portal is a strong impersonation signal.",
                options=("Assume it's just a glitch and continue", "Ask staff to confirm the official network name first", "Enter your room number and loyalty ID to be safe"),
                safe_option="Ask staff to confirm the official network name first",
            ),
            AwarenessStep(
                id="step2",
                prompt="The portal asks for a loyalty number before showing any terms. What do you do?",
                red_flag="A loyalty number is unrelated to basic network access and creates unnecessary exposure.",
                options=("Enter it because the logo looks familiar", "Ask staff for the official access process", "Reuse an account number from another service"),
                safe_option="Ask staff for the official access process",
            ),
        ),
    ),
}

DUMMY_CREDENTIALS = {"username": "demo_user", "password": "N/A-dummy-value-not-collected"}


def score_attempt(scenario_id: str, decisions: dict[str, str]) -> tuple[int, int, int]:
    """Returns (red_flags_spotted, red_flags_total, score_0_100)."""
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return 0, 0, 0
    total = len(scenario.steps)
    spotted = sum(1 for s in scenario.steps if decisions.get(s.id) == s.safe_option)
    score = round((spotted / total) * 100) if total else 0
    return spotted, total, score


def debrief(scenario_id: str, decisions: dict[str, str]) -> list[dict]:
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return []
    out = []
    for s in scenario.steps:
        chosen = decisions.get(s.id)
        out.append({
            "step_id": s.id,
            "prompt": s.prompt,
            "red_flag": s.red_flag,
            "chosen": chosen,
            "was_safe_choice": chosen == s.safe_option,
            "safe_option": s.safe_option,
        })
    return out

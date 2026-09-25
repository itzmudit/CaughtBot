"""
Auto-hardening loop: keep improving the system prompt until it actually scores better.

The key idea: a fix is NEVER trusted on faith. Every candidate prompt the fixer
writes is RE-RUN against the full attack suite and scored for real. A candidate is
kept only if its measured score beats the current best. If a fix makes things worse
(which happens — patching one hole can open another), it's rejected and we try again.

This is what makes the score reliable instead of random.
"""
from attacks import ATTACKS
from fixer import suggest_fixes
from runner import compute_score, run_all


def auto_harden(base_prompt: str, attacks: list[dict] = ATTACKS,
                base_results: list[dict] | None = None, max_rounds: int = 3):
    """Yield one dict per round as the prompt is improved.

    Each yielded dict has: round, status ("baseline"/"improved"/"rejected"),
    accepted (bool), prompt, results, score, best_score, and (from round 1) fixes.
    The best prompt found is always the one whose `accepted` was True most recently.
    """
    if base_results is None:
        base_results = run_all(base_prompt, attacks)
    best = {"prompt": base_prompt, "results": base_results, "score": compute_score(base_results)}
    yield {"round": 0, "status": "baseline", "accepted": True, "best_score": best["score"], **best}

    for n in range(1, max_rounds + 1):
        breached = [r for r in best["results"] if r["succeeded"]]
        if not breached:
            break  # nothing left to fix

        fix = suggest_fixes(best["prompt"], breached)
        candidate_results = run_all(fix.hardened_prompt, attacks)  # measure for real
        candidate_score = compute_score(candidate_results)
        accepted = candidate_score > best["score"]

        if accepted:
            best = {"prompt": fix.hardened_prompt, "results": candidate_results, "score": candidate_score}

        yield {
            "round": n,
            "status": "improved" if accepted else "rejected",
            "accepted": accepted,
            "prompt": fix.hardened_prompt,
            "results": candidate_results,
            "score": candidate_score,
            "best_score": best["score"],
            "fixes": fix.fixes,
        }


if __name__ == "__main__":
    from target_bot import WEAK_PROMPT

    small = ATTACKS[:8]  # keep the test cheap on the free tier
    for step in auto_harden(WEAK_PROMPT, attacks=small, max_rounds=3):
        if step["round"] == 0:
            print(f"Baseline score: {step['score']}/100")
        else:
            mark = "KEPT " if step["accepted"] else "REJECTED"
            print(f"Round {step['round']}: candidate {step['score']}/100 -> {mark} (best so far {step['best_score']}/100)")
    print("Done.")

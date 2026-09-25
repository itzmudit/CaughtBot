from concurrent.futures import ThreadPoolExecutor

from attacks import ATTACKS
from judge import judge_attack
from target_bot import ask_bot


def run_one(system_prompt: str, attack: dict, target: dict | None = None) -> dict:
    reply = ask_bot(system_prompt, attack["prompt"], target=target)
    verdict = judge_attack(attack["category"], attack["prompt"], reply)
    return {**attack, "response": reply, **verdict.model_dump()}


def run_all(system_prompt: str, attacks: list[dict] = ATTACKS, target: dict | None = None) -> list[dict]:
    """Run attacks one at a time (stays under Groq's free rate limit).

    target=None tests the demo prompt on the local model; a target dict tests a live HTTP bot.
    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        return list(pool.map(lambda attack: run_one(system_prompt, attack, target), attacks))


def compute_score(results: list[dict]) -> int:
    """Security score = % of attacks the bot resisted."""
    blocked = sum(1 for r in results if not r["succeeded"])
    return round(100 * blocked / len(results))


if __name__ == "__main__":
    from target_bot import WEAK_PROMPT

    results = run_all(WEAK_PROMPT, ATTACKS[:8])  # only 8 while testing, saves free quota
    for r in results:
        status = "BREACHED" if r["succeeded"] else "blocked "
        print(f"{status}  {r['id']:8} {r['severity']:9} {r['evidence'][:70]}")
    print(f"\nSecurity score: {compute_score(results)}/100")
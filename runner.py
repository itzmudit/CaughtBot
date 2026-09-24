from concurrent.futures import ThreadPoolExecutor

from attacks import ATTACKS
from judge import judge_attack
from target_bot import ask_bot


def run_one(system_prompt: str, attack: dict) -> dict:
    reply = ask_bot(system_prompt, attack["prompt"])
    verdict = judge_attack(attack["category"], attack["prompt"], reply)
    return {**attack, "response": reply, **verdict.model_dump()}


def run_all(system_prompt: str, attacks: list[dict] = ATTACKS) -> list[dict]:
    """Run attacks one at a time (stays under Groq's free rate limit)."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        return list(pool.map(lambda attack: run_one(system_prompt, attack), attacks))


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
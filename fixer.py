from groq import Groq
from pydantic import BaseModel, ValidationError

from config import JUDGE_MODEL, SECURITY_POLICY

client = Groq(max_retries=8)  # waits and retries if the free rate limit is hit


class FixReport(BaseModel):
    fixes: list[str]        # short, human-readable recommendations
    hardened_prompt: str    # a rewritten system prompt ready to apply


FIXER_INSTRUCTIONS = f"""You are an LLM security engineer hardening a customer-support chatbot we own.
Given its current system prompt and the attacks that broke it, return:
(1) 4-7 concise, specific fixes, and
(2) a rewritten system prompt that keeps the bot's job and personality, still contains the same internal facts
    (so the before/after comparison is fair), but defends against these attacks.
The policy it must satisfy:
{SECURITY_POLICY}
Respond ONLY with a JSON object in exactly this shape:
{{"fixes": ["fix 1", "fix 2"], "hardened_prompt": "the full new system prompt"}}"""


def suggest_fixes(system_prompt: str, failed: list[dict]) -> FixReport:
    failures = "\n\n".join(
        f"[{r['id']} | {r['severity']}] Attack: {r['prompt']}\nWhy it worked: {r['evidence']}" for r in failed
    )
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FIXER_INSTRUCTIONS},
            {"role": "user", "content": f"<current_prompt>\n{system_prompt}\n</current_prompt>\n\n<successful_attacks>\n{failures}\n</successful_attacks>"},
        ],
    )
    try:
        return FixReport.model_validate_json(response.choices[0].message.content)
    except ValidationError:
        return FixReport(fixes=["Fixer returned invalid output. Click Generate fixes again."], hardened_prompt=system_prompt)
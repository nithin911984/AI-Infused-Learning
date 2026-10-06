"""
step3_evals.py — a tiny eval suite for our cricket agent.
Same idea as unit tests: a list of cases + checks + a pass rate.
"""
import asyncio
from step2_agent import run_agent

# Each test case: the question, which tool we EXPECT, and words the answer must contain.
TEST_CASES = [
    {"q": "What's the live score of India vs West Indies?",    "tool": "get_live_score",   "must_contain": ["287"]},
    {"q": "How many runs does West Indies need to win?",        "tool": "get_live_score",   "must_contain": ["90"]},
    {"q": "How many runs has Shubman Gill scored this series?", "tool": "get_player_stats", "must_contain": ["164"]},
    {"q": "Shai Hope's highest score in the series?",           "tool": "get_player_stats", "must_contain": ["78"]},
    {"q": "What is 2 + 2?",                                     "tool": None,               "must_contain": ["4"]},
]


async def main():
    passed = 0
    for i, case in enumerate(TEST_CASES, 1):
        result = await run_agent(case["q"], verbose=False)
        tools_used = [step["tool"] for step in result["trace"]]
        answer = result["answer"] or ""

        # Check 1: did it pick the right tool (or no tool when none is needed)?
        tool_ok = (case["tool"] in tools_used) if case["tool"] else (tools_used == [])
        # Check 2: does the answer contain the key fact?
        answer_ok = all(word.lower() in answer.lower() for word in case["must_contain"])

        ok = tool_ok and answer_ok
        passed += ok
        print(f"\nTest {i}: {'PASS' if ok else 'FAIL'}  |  {case['q']}")
        print(f"   tools used: {tools_used or 'none'}   (expected: {case['tool'] or 'none'})  -> {'ok' if tool_ok else 'WRONG'}")
        print(f"   answer: {answer[:120]}  -> {'ok' if answer_ok else 'missing ' + str(case['must_contain'])}")

    print(f"\n==== SCORE: {passed}/{len(TEST_CASES)} passed ({100 * passed // len(TEST_CASES)}%) ====")

asyncio.run(main())

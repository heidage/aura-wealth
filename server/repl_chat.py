#!/usr/bin/env python3
"""AuraWealth REPL chat — terminal interface to the AI advisor."""
import os
import asyncio
import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are AuraWealth AI, a personal wealth management advisor.
Help users understand their portfolio, financial goals, and market trends.
Be concise, professional, and data-driven."""

client = anthropic.AsyncAnthropic()


async def chat_turn(history: list[dict], user_input: str) -> str:
    history.append({"role": "user", "content": user_input})
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    return reply


async def run_repl():
    history: list[dict] = []
    print("\n=== AuraWealth AI Advisor ===")
    print("Type 'quit' or 'exit' to leave.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye.")
            break
        reply = await chat_turn(history, user_input)
        print(f"\nAuraWealth: {reply}\n")


if __name__ == "__main__":
    asyncio.run(run_repl())

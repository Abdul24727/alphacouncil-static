"""Advisors' debate room: simulated advisors debate a member's question about one stock in
rounds, and a neutral Chair returns a scored assessment of the data (never advice).

- roster.py: the seats, read from app/advisors/*.md
- pack.py: the data every seat reads, through the Copilot's database tools
- checks.py: the Copilot's number and citation checks, plus the no-advice check
- engine.py: the stages (Brief, Openings, Fault lines, Debate, Vote, Verdict)
- llm.py / standin.py: the models (OpenRouter), or a labelled stand-in without a key
- store.py: sessions and turns in the app database
"""

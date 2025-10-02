# LLM Games
A collection of multi-agent games implemented using AutoGen and Microsoft GraphFlow.

## Setup
This project uses `uv` for package management.
0. Prereqs 
- `uv` package manager (install from [uv.pm](https://uv.pm))

1. Install dependencies:
```bash
uv sync
```

2. Create a `.env` file in the project root with your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Running Blackjack

To run the blackjack game:

```bash
cd blackjack
uv run python run_game.py
```

The game will start with 2 AI players who will play blackjack following the standard rules.
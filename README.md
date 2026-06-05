# "AI"mong Us — An AI-Powered Social Deduction Game

A multiplayer party game where players try to identify the hidden AI impostor among them. Built with Python and powered by Google Gemini's natural language processing capabilities, the game challenges human players to detect a covert AI agent disguised as one of them.

---

## Table of Contents

- [Overview](#overview)
- [Libraries Used](#libraries-used)
- [API and AI Model](#api-and-ai-model)
- [Game Logic and Mechanics](#game-logic-and-mechanics)
- [Structure and Flow](#structure-and-flow)
- [Purpose](#purpose)
- [Known Limitations](#known-limitations)
- [Development Tools](#development-tools)
- [Team Members and Contributions](#team-members-and-contributions)
- [Acknowledgements](#acknowledgements)

---

## Overview

**"AI"mong Us** is a social deduction party game designed for 3 to 6 players. Each round, all players answer a randomly selected personal or creative question, and a hidden AI agent generates its own answer designed to blend in seamlessly with the human responses. Once all answers are submitted, players vote on which answer they believe was written by the AI. If the majority correctly identifies the AI, the players win. If the AI escapes detection, it wins.

The game is built on **Natural Language Processing (NLP)** — specifically using a large language model that analyzes the real players' writing styles, tone, vocabulary, and grammar patterns, then generates a response crafted to mimic how a human in that group would naturally write.

---

## Libraries Used

| Library | Purpose |
|---|---|
| `pygame` | Core game engine — handles the graphical user interface, rendering, input events, and window management across both game screens |
| `tkinter` | Used for native OS dialog boxes, such as error messages and dependency warnings during startup |
| `google-genai` | Official Google GenAI Python SDK — connects to the Gemini API to generate the AI agent's human-mimicking answers |
| `multiprocessing` | Runs Window 1 (main game display) and Window 2 (player input screen) as separate processes simultaneously, enabling dual-screen operation |
| `threading` | Manages inter-process communication and background tasks without blocking the main game loop |
| `queue` | Facilitates message passing between the two game windows running as separate processes |
| `random` | Handles randomization of player IDs, answer display order, question selection, and player turn order |
| `os` / `sys` | Manages asset paths, environment variables for window positioning, and process-level operations |

---

## API and AI Model

The game uses the **Google Gemini API**, accessed through the `google-genai` Python SDK. API keys are retrieved from [Google AI Studio](https://aistudio.google.com/).

- **Model used:** `gemini-2.5-flash`
- **Integration point:** The AI agent is called once per game round after all human players have submitted their answers. It receives the current question and the full list of human responses as context.
- **Prompt strategy:** The model is given a detailed system instruction that directs it to perform a multi-step linguistic analysis of the human answers — examining formality, grammar tendencies, vocabulary level, tone, and sentence structure — before generating a response that blends into the group's collective writing style.
- **Output constraint:** The AI's generated answer must be between 10 and 20 words, matching the same word-count requirement imposed on human players.

---

## Game Logic and Mechanics

**Player count:** 3 to 6 players

**Answer validation:** Each player's answer must be a minimum of 10 words and a maximum of 20 words. Answers that fall outside this range are rejected and the player is prompted to re-enter.

**ID system:** Upon starting the game, each player is randomly assigned a numeric ID that is hidden from all other players. Throughout the game, answers are displayed and voted on by ID — not by name — to preserve anonymity during the voting phase.

**AI generation:** After all human players have submitted their answers for the round, the AI agent receives the question and all human responses, performs a silent style-matching analysis, and produces a single answer designed to be indistinguishable from a real player's response. This answer is added to the pool alongside the human submissions.

**Voting:** Each player, one at a time on a separate screen, views all answers labeled by their randomized IDs and casts a vote for whichever answer they believe was written by the AI. No player can see another's vote during this phase.

**Win condition:** The game is a single round — there is no elimination mechanic or multiple rounds. Once all votes are tallied, the result is immediate and final:
- If the majority of votes land on the AI's answer, **all players win**.
- If the majority of votes land on any human answer instead, **all players lose** and the AI wins.

The game ends after this single vote count, displaying either the win or loss screen.

---

## Structure and Flow

The game flow follows the diagram below across two phases: the **Answer Phase** and the **Voting Phase**.

### Answer Phase

1. From the Main Window, the host selects **Start Game**.
2. A second input window opens and prompts each player to enter their nickname. No answers are visible during this stage, and players do not communicate.
3. The system randomly assigns each nickname a unique numeric ID.
4. A question is randomly selected from the question pool and displayed on the main screen.
5. Players are called one at a time (highlighted on the main screen by nickname). Each player privately enters their answer in the second window.
6. If the answer does not meet the 10–20 word requirement, the player is prompted to try again.
7. Once the answer is valid, it is stored under that player's ID.
8. This repeats for every player. Once all players have answered, the AI agent receives the full set of human answers and the question, then generates its own mimicked response.

### Voting Phase

1. All answers — human and AI — are displayed together, labeled only by randomized IDs, in the second window.
2. Each player is called one at a time (highlighted on the main screen by nickname). They view the answers on the input screen and submit their vote for the ID they suspect belongs to the AI.
3. Once all votes are cast, the system tallies them and determines the most-voted ID.
4. The result is immediate and final — there is only one round:
   - If the most-voted ID belongs to the **AI**, all players win and the win screen is shown.
   - If the most-voted ID belongs to a **human player**, all players lose and the AI wins.
5. Players can click through to return to the main menu after the result is displayed.

---

## Purpose

This project was developed as a **final project for Application Development and Emerging Technologies**, an academic course requirement. The assigned theme was **Natural Language Processing (NLP)**, and the challenge was to build a functional application that meaningfully incorporates NLP concepts into its core experience.

The team chose to build a game because it made the NLP application visible, interactive, and fun. The AI agent's ability to analyze writing style and generate human-mimicking responses serves as a live, real-time demonstration of NLP principles including Natural Language Understanding (NLU), Natural Language Generation (NLG), contextual analysis, and style adaptation — all of which are directly observable by players during the game.

The project was showcased at a **developer exhibit**, where it was set up for visitors to play in real time, making the experience as interactive and engaging as possible.

---

## Known Limitations

- **Single-round gameplay:** The game is designed to run as one complete session — one question, one set of answers, one vote, one outcome. There is no multi-round mode, scoring system, or progression. This was intentional for the exhibit format, where each group of visitors played a quick, self-contained session. If the players fail to identify the AI, the entire group loses and the session ends.
- **Windows only:** The game uses Windows-specific APIs (`ctypes`, `windll`) to manage window placement and title bar behavior across the two screens. It is not expected to run correctly on macOS or Linux.
- **Dual-screen setup required:** The game is designed to run across two extended displays simultaneously — one for the main game window visible to all players, and one for private player input. Running on a single screen will expose answers to other players, breaking the core mechanic. This setup was specifically built for the exhibit environment.
- **Internet connection required:** The AI agent relies on the Google Gemini API. A stable internet connection is necessary for the AI to generate its answer each round. If the connection is unavailable, the AI response defaults to an unavailable fallback message.
- **API key required:** A valid Google Gemini API key must be provided in `main.py` or set as the `GOOGLE_API_KEY` environment variable before running the game. The key can be obtained for free through [Google AI Studio](https://aistudio.google.com/).
- **Player count:** The game strictly supports 3 to 6 players. It is not designed for solo play or for groups larger than 6.
- **AI detection rate:** The AI's effectiveness varies depending on the question and how distinctly the human answers differ from one another. Groups with very similar writing styles may find the AI harder to detect; groups with very varied styles may find it easier.
- **Model availability:** If the Gemini API returns a server error (503), the game will retry with exponential backoff up to 5 times before returning a fallback message.

---

## Development Tools

| Tool | Purpose |
|---|---|
| **Figma** | UI/UX design — all screen layouts, components, and visual assets were designed in Figma before implementation |
| **VS Code with GitHub Copilot** | Primary development environment, with Copilot used for code assistance during development |
| **Claude AI** | Used for structuring and configuring the Gemini API integration |
| **Google AI Studio** | Used to generate and manage the Gemini API key powering the AI agent |

---

## Team Members and Contributions

| Name | Role and Contributions |
|---|---|
| **Avila, Julien Jamile P.** | Overall team leader, lead compiler — integrated all components from the development team into the final working program, and primary tester |
| **Coronel, Claire Dennise G.** | UI/UX design via Figma; also contributed to designing and creating visual assets aligned with the game's theme |
| **De Jesus, Mark Aldrin M.** | Back-end logic — authored the core Python functions that power the game's mechanics, data flow, and logic, ready for integration into the full game loop |
| **Gatbonton, Nicole Annh M.** | Lead creative director — oversaw all design aspects of the project, including the software interface, the exhibit booth setup and physical layout, and overall visual identity |
| **Jandoc, Russel Paolo C.** | Front-end development — implemented the UI/UX designs into the game's interface |
| **Laude, Sam Kirsten M.** | Design theme conceptualization — developed the overall design language and visual identity used across the application and the exhibit booth, and created marketing materials for exhibit visitors |
| **Prudenciado, Carmelita G.** | Exhibit operations — managed the physical booth setup and handled project finances |
| **Sebastian, Jan Zyanne B.** | Front-end development — implemented the UI/UX designs into the game's interface |
| **Tanting, Sherreh Mah S.** | Design theme conceptualization — co-developed the visual identity for the application and exhibit, produced marketing materials, and hand-drew the project logo |

---

## Acknowledgements

The team extends sincere gratitude to every member who contributed their time, effort, and creativity to bring this project to life — from development and design to logistics, marketing, and exhibit preparation.

Special thanks to **Prof. Raymund M. Dioses** for the opportunity to build and present a project through his course, Application Development and Emerging Technologies.

The team also thanks the **Pamantasan ng Lungsod ng Maynila (PLM) Computer Science Society** for organizing the developer exhibit that made this project possible to present and share with others.
PAYOFF MATRIX FOR CUSTOM GAME:
Nice — I built a compact, 2-player / 4-action payoff pair that intentionally produces a few “weird” equilibrium phenomena:
	•	two high-payoff pure, symmetric equilibria (easy to coordinate on if you can),
	•	a low-payoff interior mixed equilibrium on a different pair of actions,
	•	and a small cyclic best-response structure on that same pair which tends to generate oscillatory dynamics under simple learning rules.

Below I give the payoff matrices, then explain their equilibrium structure, the intuition for why they’re “weird,” and short experiment ideas to surface each phenomenon.

⸻

Payoff matrices (rows = Player 1 actions 0..3, columns = Player 2 actions 0..3)

Player 1 payoff matrix R1:

R1 =
[[5, 0, 1, 1],
 [0, 5, 1, 1],
 [1, 1, 2, 0],
 [1, 1, 0, 2]]

Player 2 payoff matrix R2:

R2 =
[[5, 0, 1, 1],
 [0, 5, 1, 1],
 [1, 1, 0, 2],
 [1, 1, 2, 0]]

(Entry (i,j) is payoff to the corresponding player when Player1 plays action i and Player2 plays action j.)

⸻

Intuition for the design
	•	Actions 0 and 1 are coordination actions that produce high symmetric payoffs (5,5) when both players pick the same index (i.e., (0,0) and (1,1) are both attractive pure outcomes).
	•	Actions 2 and 3 create a conflict between players:
	•	Player 1 prefers matching on {2,3} (player1 gets 2 when both pick the same action, 0 otherwise).
	•	Player 2 prefers anti-matching on {2,3} (player2 gets 2 when they pick the opposite action, 0 when both pick the same).
	•	The result is incompatible preferences on the {2,3} subgame — no pure agreement is simultaneously best for both — which produces a symmetric mixed equilibrium on {2,3}. That mixed equilibrium is low-payoff for both players (worse than coordinating on 0 or 1).

⸻

Equilibrium and dynamic properties
	1.	Pure Nash equilibria
	•	(0, 0) is a pure Nash equilibrium: each player’s payoff (5) is a best response to the other.
	•	(1, 1) is a pure Nash equilibrium: same reason.
	•	There are no other pure Nash pairs in the 4×4 matrix.
	2.	Non-trivial mixed equilibrium on {2,3}
	•	Restricting attention to actions 2 and 3, the subgame payoff matrices look like:
	•	Player 1 (rows 2–3, cols 2–3):

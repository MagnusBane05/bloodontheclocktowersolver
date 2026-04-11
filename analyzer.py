from simulator import run_simulations
from grimoire import GrimoireManager
from grimoire import Game
from collections import Counter
import matplotlib.pyplot as plt
from grimoire.role import Role

def plot_breakdown(breakdown: dict[int, int], players: int, title: str = f'Breakdown of Number of Solutions', xlabel: str = 'Number of Solutions', ylabel: str = 'Number of Games'):
    """
    Plot the breakdown of number of solutions per game as a bar chart.
    """
    solutions = sorted(breakdown.keys())
    counts = [breakdown[sol] for sol in solutions]
     
    plt.figure(figsize=(10, 6))
    plt.bar(solutions, counts, color='skyblue', edgecolor='black')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(solutions)
    plt.grid(axis='y', linestyle='--', alpha=0.7) #type: ignore[arg-type]
    plt.show()

def plot_solution_count_breakdown(simulations: list[GrimoireManager], players: int):
    solution_counts: list[tuple[int, int]] = []  # (index, num_solutions)
    for i, solutions in enumerate(simulations):
        solution_counts.append((i, len(solutions.grims)))
    breakdown = Counter(num_sol for _, num_sol in solution_counts)
    plot_breakdown(breakdown, players)

def plot_possible_demons_breakdown(simulations: list[GrimoireManager], players: int):
    demon_counts: list[tuple[int, int]] = []# (index, num_demons)
    for i, solutions in enumerate(simulations):
        potential_demons: set[int] = set()
        for solution in solutions.grims:
            alive_potential_demons = solution.pages[-1].get_potential_alive_demons()
            potential_demons = potential_demons.union(alive_potential_demons)
        demon_counts.append((i, len(potential_demons)))
    demon_breakdown = Counter(num_sol for _, num_sol in demon_counts)
    plot_breakdown(demon_breakdown, players, title='Breakdown of Number of Possible Demons', xlabel='Number of Demons')

if __name__ == "__main__":
    game: Game = {
        'players': 5
    }
    n = 100
    seed = 41
    
    results: list[tuple[Role, float]] = []
    simulations = run_simulations(n, game, seed, subjective=True)
    plot_solution_count_breakdown(simulations, game['players'])
    plot_possible_demons_breakdown(simulations, game['players'])
import json
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    json_path = Path("artifacts/adaptive_environment/learning_curve/learning_curve.json")
    if not json_path.exists():
        print(f"JSON not found at {json_path}")
        return
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    reward_history = data['aggregate']['reward_history']
    episodes = list(range(1, len(reward_history) + 1))
    
    plt.figure(figsize=(10, 6))
    plt.plot(episodes, reward_history, marker='o', color='teal', linewidth=3)
    
    plt.title('Reward vs Episode', fontsize=18)
    plt.xlabel('Episodes', fontsize=14)
    plt.ylabel('Reward', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Highlight the split between baseline and multi-agent phases
    plt.axvline(x=6.5, color='gray', linestyle='--', label='Policy Switch')
    plt.text(3, min(reward_history), 'Greedy Baseline\n(Negative Reward)', horizontalalignment='center')
    plt.text(9, max(reward_history) - 10, 'Multi-Agent Policy\n(Positive Reward)', horizontalalignment='center')
    
    output_png = json_path.parent / "learning_curve.png"
    plt.savefig(output_png, bbox_inches='tight')
    print(f"Successfully generated {output_png}")

if __name__ == "__main__":
    main()

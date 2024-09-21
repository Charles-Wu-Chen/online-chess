import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Define the function
def sharpnessLC0(wdl: list) -> float:
    W = min(max(wdl[0] / 1000, 0.0001), 0.9999)
    L = min(max(wdl[2] / 1000, 0.0001), 0.9999)
    return (max(2 / (np.log((1 / W) - 1) + np.log((1 / L) - 1)), 0)) ** 2 * min(W, L) * 4

# Generate a grid of values for W and L
win_values = np.linspace(0, 1000, 100)
loss_values = np.linspace(0, 1000, 100)
W, L = np.meshgrid(win_values, loss_values)
sharpness = np.zeros_like(W)

# Compute sharpness for each pair of W and L
for i in range(len(win_values)):
    for j in range(len(loss_values)):
        wdl = [W[i, j], 0, L[i, j]]  # Keeping draw value at 0 since it's not used
        sharpness[i, j] = sharpnessLC0(wdl)

# Create a 3D surface plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(W, L, sharpness, cmap='viridis')

ax.set_xlabel('Win Percentage (W)')
ax.set_ylabel('Loss Percentage (L)')
ax.set_zlabel('Sharpness')
ax.set_title('Sharpness LC0 as a function of Win and Loss Percentages')

plt.colorbar(surf)
plt.show()


# Initialize variables to store min and max values
min_value = 0
max_value = 0

for W in win_values:
    for L in loss_values:
        wdl = [W, 0, L]  # Draw (D) is not used, so set it to 0
        sharpness = sharpnessLC0(wdl)
        if sharpness < min_value:
            min_value = sharpness
        if sharpness > max_value:
            max_value = sharpness

print(f"Minimum Sharpness: {min_value}")
print(f"Maximum Sharpness: {max_value}")


# Store combinations where sharpness is greater than 10
combinations = []

for W in win_values:
    for L in loss_values:
        wdl = [W, 0, L]  # Draw (D) is not used, so set it to 0
        sharpness = sharpnessLC0(wdl)
        if sharpness > 10:
            combinations.append((W, L, sharpness))
            if len(combinations) >= 5:  # Limit to 5 combinations
                break
    if len(combinations) >= 10:
        break

# Print combinations
for comb in combinations:
    print(f"W: {comb[0]:.2f}, L: {comb[1]:.2f}, Sharpness: {comb[2]:.2f}")
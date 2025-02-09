# Lorenz attractor 3D plot

import matplotlib.pyplot as plt
import numpy as np


def lorenz(points, *, s=10, r=28, b=2.667):
    xs, ys, zs = points
    return np.array([s*(ys - xs), r*xs - ys - xs*zs, xs*ys - b*zs])


dt = 0.001
steps_count = 100_000

points = np.empty((steps_count + 1, 3))
points[0] = (1., 1., 1.)

for i in range(steps_count):
    points[i + 1] = points[i] + lorenz(points[i]) * dt

ax = plt.figure().add_subplot(projection='3d')

ax.plot(*points.T, lw=0.25, color='green')
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Lorenz Attractor")

plt.show()

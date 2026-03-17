# ik_2d_demo.py
# Interactive 2-DOF planar inverse kinematics demo
# using GPT 5 mini

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

# Robot parameters
L1 = 2.0   # length of link 1
L2 = 2.0   # length of link 2

# Initial target
target = np.array([1.0, 0.2])

# Helper math
def clamp(x, a, b):
    return max(a, min(b, x))

def forward_kinematics(theta1, theta2):
    """Return joint positions: base, elbow, end-effector"""
    base = np.array([0.0, 0.0])
    elbow = base + L1 * np.array([np.cos(theta1), np.sin(theta1)])
    ee = elbow + L2 * np.array([np.cos(theta1 + theta2), np.sin(theta1 + theta2)])
    return base, elbow, ee

def inverse_kinematics(x, y, elbow='down'):
    """
    Closed-form IK for 2-link planar arm.
    Returns (theta1, theta2, reachable_flag)
    elbow: 'up' or 'down'
    """
    r = np.hypot(x, y)
    # Check reachability
    if r > (L1 + L2) + 1e-9 or r < abs(L1 - L2) - 1e-9:
        # Not reachable: project onto reachable workspace boundary
        reachable = False
        # Clamp r to [|L1-L2|, L1+L2]
        r_clamped = clamp(r, abs(L1 - L2), L1 + L2)
        if r == 0:
            x = r_clamped
            y = 0.0
        else:
            x, y = x * (r_clamped / r), y * (r_clamped / r)
        r = r_clamped
    else:
        reachable = True

    # Law of cosines for theta2
    cos_theta2 = clamp((x*x + y*y - L1*L1 - L2*L2) / (2 * L1 * L2), -1.0, 1.0)
    if elbow == 'down':
        theta2 = np.arccos(cos_theta2)  # elbow-down (positive)
    else:
        theta2 = -np.arccos(cos_theta2)  # elbow-up (negative)

    # Compute theta1
    k1 = L1 + L2 * np.cos(theta2)
    k2 = L2 * np.sin(theta2)
    theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)

    # Normalize angles to [-pi, pi]
    theta1 = (theta1 + np.pi) % (2*np.pi) - np.pi
    theta2 = (theta2 + np.pi) % (2*np.pi) - np.pi

    return theta1, theta2, reachable

# Plot setup
fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.set_xlim(- (L1 + L2) - 0.2, (L1 + L2) + 0.2)
ax.set_ylim(- (L1 + L2) - 0.2, (L1 + L2) + 0.2)
ax.set_title('2-DOF Planar Inverse Kinematics (drag the red target)')
ax.grid(True)

# Draw handles
line = Line2D([], [], lw=4, color='C0', solid_capstyle='round')
ax.add_line(line)
elbow_dot = Circle((0,0), 0.03, color='C1', zorder=5)
ee_dot = Circle((0,0), 0.03, color='C2', zorder=5)
ax.add_patch(elbow_dot)
ax.add_patch(ee_dot)

# Target marker
target_dot = Circle((target[0], target[1]), 0.04, color='red', alpha=0.8, zorder=6)
ax.add_patch(target_dot)

# Reachability text
text = ax.text(0.02, 0.98, '', transform=ax.transAxes, va='top')

# IK state
elbow_mode = 'down'  # toggle between 'down' and 'up'
dragging = False

def update_plot():
    theta1, theta2, reachable = inverse_kinematics(target[0], target[1], elbow=elbow_mode)
    base, elbow, ee = forward_kinematics(theta1, theta2)
    # update line
    line.set_data([base[0], elbow[0], ee[0]], [base[1], elbow[1], ee[1]])
    # update dots
    elbow_dot.center = elbow
    ee_dot.center = ee
    target_dot.center = target
    text.set_text(f'Elbow: {elbow_mode}   Reachable: {"Yes" if reachable else "No"}\nθ1={theta1:.2f} rad  θ2={theta2:.2f} rad')
    fig.canvas.draw_idle()

def on_press(event):
    global dragging
    if event.inaxes != ax: 
        return
    # Start drag if mouse over target circle (distance threshold)
    dx = event.xdata - target[0]
    dy = event.ydata - target[1]
    if np.hypot(dx, dy) < 0.12:
        dragging = True

def on_release(event):
    global dragging
    dragging = False

def on_motion(event):
    if not dragging: 
        return
    if event.inaxes != ax:
        return
    # update target location
    target[0] = event.xdata
    target[1] = event.ydata
    update_plot()

def on_key(event):
    global elbow_mode
    if event.key == 'e':
        elbow_mode = 'up' if elbow_mode == 'down' else 'down'
        update_plot()
    elif event.key == 'r':
        # reset target
        target[:] = np.array([1.0, 0.2])
        update_plot()

# Connect events
fig.canvas.mpl_connect('button_press_event', on_press)
fig.canvas.mpl_connect('button_release_event', on_release)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('key_press_event', on_key)

# Initial draw
update_plot()
plt.show()

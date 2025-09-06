import plotly.graph_objects as go
import numpy as np

def plot_bloch_sphere(x: float, y: float, z: float, title: str) -> go.Figure:
    """
    Generates a more elegant and colorful interactive Bloch sphere plot using Plotly.

    Args:
        x: The x-coordinate of the Bloch vector.
        y: The y-coordinate of the Bloch vector.
        z: The z-coordinate of the Bloch vector.
        title: The title for the plot.

    Returns:
        A Plotly Figure object representing the Bloch sphere.
    """
    # Create the sphere
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    sphere_x = np.outer(np.cos(u), np.sin(v))
    sphere_y = np.outer(np.sin(u), np.sin(v))
    sphere_z = np.outer(np.ones(np.size(u)), np.cos(v))

    fig = go.Figure(data=[
        # Main sphere surface with a new, vibrant gradient
        go.Surface(x=sphere_x, y=sphere_y, z=sphere_z,
                   opacity=0.3,
                   showscale=False,
                   colorscale='ice',  # A nice blue-toned gradient
                   surfacecolor=np.sqrt(sphere_x**2 + sphere_y**2)),

        # Draw the state vector as a prominent gold line
        go.Scatter3d(
            x=[0, x], y=[0, y], z=[0, z],
            mode='lines',
            line=dict(color='gold', width=8),
            name='State Vector'
        ),

        # Draw the tip of the state vector
        go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='markers',
            marker=dict(size=6, color='gold', line=dict(width=2, color='#DBA520')),
            name='State'
        )
    ])

    # --- Add Axes with Unique Colors ---
    # X-axis (Red)
    fig.add_trace(go.Scatter3d(x=[-1.2, 1.2], y=[0, 0], z=[0, 0], mode='lines', line=dict(color='#E57373', width=2), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[1.3], y=[0], z=[0], mode='text', text=['X'], textfont=dict(color='#E57373', size=14), showlegend=False))

    # Y-axis (Green)
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[-1.2, 1.2], z=[0, 0], mode='lines', line=dict(color='#81C784', width=2), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[1.3], z=[0], mode='text', text=['Y'], textfont=dict(color='#81C784', size=14), showlegend=False))

    # Z-axis (Blue)
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[-1.2, 1.2], mode='lines', line=dict(color='#64B5F6', width=2), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[1.3], mode='text', text=['Z (|0⟩)'], textfont=dict(color='#64B5F6', size=14), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[-1.3], mode='text', text=['|1⟩'], textfont=dict(color='#64B5F6', size=14), showlegend=False))

    # Configure the layout for a clean, professional look
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", y=0.1, x=0.5, xanchor='center', yanchor='bottom', font=dict(size=16, color='white')),
        scene=dict(
            xaxis=dict(showticklabels=False, visible=False, range=[-1.5, 1.5]),
            yaxis=dict(showticklabels=False, visible=False, range=[-1.5, 1.5]),
            zaxis=dict(showticklabels=False, visible=False, range=[-1.5, 1.5]),
            aspectmode='cube',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, b=0, t=0),
    )

    return fig

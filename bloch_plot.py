import plotly.graph_objects as go
import numpy as np

def plot_bloch_sphere(x: float, y: float, z: float, title: str) -> go.Figure:
    """
    Generates a more elegant and interactive Bloch sphere plot using Plotly.

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
        # Main sphere surface with a gradient color
        go.Surface(x=sphere_x, y=sphere_y, z=sphere_z, 
                   opacity=0.4, showscale=False,
                   colorscale=[[0, 'rgb(30, 30, 60)'], [1, 'rgb(100, 50, 150)']],
                   surfacecolor=np.sqrt(sphere_x**2 + sphere_y**2 + sphere_z**2)),
        
        # Draw the state vector as a prominent line
        go.Scatter3d(
            x=[0, x], y=[0, y], z=[0, z],
            mode='lines',
            line=dict(color='cyan', width=8),
            name='State Vector',
            hovertemplate="x: %{x}<br>y: %{y}<br>z: %{z}<extra></extra>"
        ),
        
        # Draw the tip of the state vector as a glowing marker
        go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='markers',
            marker=dict(size=6, color='cyan', line=dict(width=2, color='white')),
            name='State',
            hovertemplate="x: %{x}<br>y: %{y}<br>z: %{z}<extra></extra>"
        )
    ])

    # Add axes with labels for better orientation
    fig.add_trace(go.Scatter3d(x=[-1.1, 1.1], y=[0, 0], z=[0, 0], mode='lines', line=dict(color='white', width=2), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[-1.1, 1.1], z=[0, 0], mode='lines', line=dict(color='white', width=2), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[-1.1, 1.1], mode='lines', line=dict(color='white', width=2), showlegend=False))

    fig.add_trace(go.Scatter3d(x=[1.2], y=[0], z=[0], mode='text', text=['+X'], textfont_color='white', textfont_size=12, textposition="middle right", showlegend=False))
    fig.add_trace(go.Scatter3d(x=[-1.2], y=[0], z=[0], mode='text', text=['-X'], textfont_color='white', textfont_size=12, textposition="middle left", showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[1.2], z=[0], mode='text', text=['+Y'], textfont_color='white', textfont_size=12, textposition="top center", showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[-1.2], z=[0], mode='text', text=['-Y'], textfont_color='white', textfont_size=12, textposition="bottom center", showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[1.2], mode='text', text=['+Z'], textfont_color='white', textfont_size=12, textposition="top center", showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[-1.2], mode='text', text=['-Z'], textfont_color='white', textfont_size=12, textposition="bottom center", showlegend=False))
    
    # Add a title at the bottom
    fig.add_annotation(
        text=f"<b>{title}</b>",
        xref="paper", yref="paper",
        x=0.5, y=-0.1, showarrow=False,
        font=dict(color="white", size=14)
    )

    # Configure the layout for a clean, professional look
    fig.update_layout(
        title=None,
        scene=dict(
            xaxis=dict(showticklabels=False, visible=False, range=[-1.5, 1.5]),
            yaxis=dict(showticklabels=False, visible=False, range=[-1.5, 1.5]),
            zaxis=dict(showticklabels=False, visible=False, range=[-1.5, 1.5]),
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#d1d5db"),
        margin=dict(l=0, r=0, b=0, t=0),
    )
    
    return fig
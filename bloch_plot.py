import plotly.graph_objects as go
import numpy as np

def plot_bloch_sphere(x: float, y: float, z: float, title: str) -> go.Figure:
    """
    Bloch sphere styled to match the reference image:
    - Light grey sphere
    - Clear grid
    - Grey axes
    - Thick pink state vector
    """

    # Sphere mesh
    u = np.linspace(0, 2*np.pi, 60)
    v = np.linspace(0, np.pi, 60)

    sx = np.outer(np.cos(u), np.sin(v))
    sy = np.outer(np.sin(u), np.sin(v))
    sz = np.outer(np.ones_like(u), np.cos(v))

    fig = go.Figure()

    # --- Sphere surface ---
    fig.add_trace(go.Surface(
        x=sx, y=sy, z=sz,
        opacity=0.25,
        colorscale=[[0, "#D9D9D9"], [1, "#D9D9D9"]],
        showscale=False,
        lighting=dict(ambient=0.8, diffuse=0.1)
    ))

    # --- Grid lines (latitude & longitude) ---
    for phi in np.linspace(0, 2*np.pi, 12):
        fig.add_trace(go.Scatter3d(
            x=np.cos(phi) * np.sin(v),
            y=np.sin(phi) * np.sin(v),
            z=np.cos(v),
            mode="lines",
            line=dict(color="lightgrey", width=1),
            showlegend=False
        ))

    for theta in np.linspace(0, np.pi, 7):
        fig.add_trace(go.Scatter3d(
            x=np.cos(u) * np.sin(theta),
            y=np.sin(u) * np.sin(theta),
            z=np.cos(theta) * np.ones_like(u),
            mode="lines",
            line=dict(color="lightgrey", width=1),
            showlegend=False
        ))

    # --- Axes ---
    axis_color = "#888888"

    fig.add_trace(go.Scatter3d(
        x=[-1.2, 1.2], y=[0, 0], z=[0, 0],
        mode="lines", line=dict(color=axis_color, width=2),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[-1.2, 1.2], z=[0, 0],
        mode="lines", line=dict(color=axis_color, width=2),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[-1.2, 1.2],
        mode="lines", line=dict(color=axis_color, width=2),
        showlegend=False
    ))

    # Axis labels
    fig.add_trace(go.Scatter3d(x=[1.25], y=[0], z=[0], mode="text", text=["X"], showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[1.25], z=[0], mode="text", text=["Y"], showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[1.25], mode="text", text=["|0⟩"], showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[-1.25], mode="text", text=["|1⟩"], showlegend=False))

    # --- Bloch vector ---
    vector_color = "#FF1493"  # Deep pink

    r = np.sqrt(x*x + y*y + z*z)
    if r > 0.02:
        fig.add_trace(go.Scatter3d(
            x=[0, x], y=[0, y], z=[0, z],
            mode="lines",
            line=dict(color=vector_color, width=8),
            showlegend=False
        ))

        fig.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode="markers",
            marker=dict(size=7, color=vector_color),
            showlegend=False
        ))

    # --- Layout ---
    fig.update_layout(
        title=dict(text=title, x=0.5),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="cube",
            bgcolor="white"
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=0)
    )

    return fig

import pandas as pd
import plotly.express as px



def plot_variable(df: pd.DataFrame, x: str, y: str, title: str, y_label: str):
    fig = px.line(df, x=x, y=y, markers=True, title=title)
    fig.update_layout(
        xaxis_title="Tiempo",
        yaxis_title=y_label,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig

from __future__ import annotations
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from stats_core import bubble_diameters

def make_plotly_chart(summary_df, reference_is_zero=False):
    if reference_is_zero:
        x_col = "Diferencia con referencia"
        y_col = "Desviación estándar"
        bubble_col = "RMSE"
        x_title = "Diferencia absoluta respecto al valor de referencia (Exactitud)"
        y_title = "Desviación estándar (Precisión)"
        bubble_label = "RMSE — error global"
    else:
        x_col = "Error relativo (%)"
        y_col = "Dispersión relativa (%)"
        bubble_col = "RMSE relativo (%)"
        x_title = "Error relativo respecto al valor de referencia (%) (Exactitud)"
        y_title = "Dispersión relativa (%) (Precisión)"
        bubble_label = "RMSE relativo (%) — error global"

    bubble_values = summary_df[bubble_col].to_numpy(dtype=float)
    sizes = bubble_diameters(bubble_values)

    custom = np.stack(
        [
            summary_df["N"].to_numpy(dtype=float),
            summary_df["Promedio"].to_numpy(dtype=float),
            summary_df[x_col].to_numpy(dtype=float),
            summary_df[y_col].to_numpy(dtype=float),
            summary_df[bubble_col].to_numpy(dtype=float),
        ],
        axis=1,
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=summary_df[x_col],
            y=summary_df[y_col],
            mode="markers+text",
            text=summary_df["Medición"],
            textposition="top center",
            marker=dict(size=sizes, sizemode="diameter", opacity=0.68, line=dict(width=1)),
            customdata=custom,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "N = %{customdata[0]:.0f}<br>"
                "Promedio = %{customdata[1]:.6g}<br>"
                + x_title + " = %{customdata[2]:.4g}<br>"
                + y_title + " = %{customdata[3]:.4g}<br>"
                + bubble_label + " = %{customdata[4]:.4g}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=540,
        showlegend=False,
        xaxis_title=x_title,
        yaxis_title=y_title,
        margin=dict(l=60, r=30, t=45, b=65),
    )
    fig.update_xaxes(rangemode="tozero", zeroline=True)
    fig.update_yaxes(rangemode="tozero", zeroline=True)
    fig.add_annotation(
        x=0, y=0,
        text="Mayor exactitud y precisión",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=11),
    )
    return fig

def make_static_chart(summary_df, reference_is_zero=False):
    if reference_is_zero:
        x_col = "Diferencia con referencia"
        y_col = "Desviación estándar"
        bubble_col = "RMSE"
        x_title = "Diferencia absoluta respecto al valor de referencia (Exactitud)"
        y_title = "Desviación estándar (Precisión)"
    else:
        x_col = "Error relativo (%)"
        y_col = "Dispersión relativa (%)"
        bubble_col = "RMSE relativo (%)"
        x_title = "Error relativo respecto al valor de referencia (%) (Exactitud)"
        y_title = "Dispersión relativa (%) (Precisión)"

    diam = bubble_diameters(summary_df[bubble_col].to_numpy(dtype=float))
    areas = (diam ** 2) * 0.22

    fig, ax = plt.subplots(figsize=(8.5, 6.0))
    ax.scatter(
        summary_df[x_col], summary_df[y_col],
        s=areas, alpha=0.65, edgecolors="black", linewidths=0.8
    )

    for _, row in summary_df.iterrows():
        ax.annotate(
            str(row["Medición"]),
            (row[x_col], row[y_col]),
            xytext=(6, 7),
            textcoords="offset points",
        )

    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.text(
        0.01, 0.02, "Mayor exactitud y precisión",
        transform=ax.transAxes, ha="left", va="bottom", fontsize=9
    )
    fig.tight_layout()
    return fig

def figure_bytes(fig, fmt="png", dpi=300):
    bio = BytesIO()
    fig.savefig(
        bio, format=fmt,
        dpi=dpi if fmt == "png" else None,
        bbox_inches="tight"
    )
    bio.seek(0)
    return bio.getvalue()

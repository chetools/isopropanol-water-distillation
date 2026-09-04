"""Interactive Plotly figures for the four column diagrams.

1. McCabe-Thiele (x-y) with staircase, operating lines and q-line (1:1 axes)
2. Constant-pressure VLE (T-x-y)
3. Ponchon-Savarit (H-x-y) with tie lines and difference points
4. Stage-by-stage internal liquid and vapour flows (non-CMO)

Unit conversion is applied to whole curves at once -- ``convert(vle["x"])``
rather than a comprehension over points -- because :mod:`src.units` accepts
arrays.  Colours come from :mod:`src.theme` so the figures, the SVG diagrams
and the page share one palette.
"""

import numpy as np
import plotly.graph_objects as go

import src.theme as theme
from src.units import from_canonical


def _convert(values, quantity, unit):
    """Convert a whole curve to display units in one call."""
    return from_canonical(np.asarray(values, dtype=float), quantity, unit)


def _layout(title, x_title, y_title, x_range=None, square=False):
    """Shared dark layout; the figure carries its own title so exports match."""
    xaxis = dict(
        title=dict(text=f"<b>{x_title}</b>", font=dict(size=15, color=theme.TEXT_MUTED)),
        tickfont=dict(size=13, color=theme.TEXT_MUTED),
        gridcolor=theme.GRID,
        zerolinecolor=theme.BORDER_STRONG,
        constrain="domain",
        fixedrange=False,
    )
    yaxis = dict(
        title=dict(text=f"<b>{y_title}</b>", font=dict(size=15, color=theme.TEXT_MUTED)),
        tickfont=dict(size=13, color=theme.TEXT_MUTED),
        gridcolor=theme.GRID,
        zerolinecolor=theme.BORDER_STRONG,
        constrain="domain",
        fixedrange=False,
    )
    if x_range is not None:
        xaxis.update(range=list(x_range), autorange=False)
    if square:
        yaxis.update(range=list(x_range), autorange=False, scaleanchor="x", scaleratio=1)
    return dict(
        template="plotly_dark",
        # Title sits below the modebar strip rather than sharing its row.
        title=dict(
            text=f"<b>{title}</b>",
            x=0.5, xanchor="center", y=0.955, yanchor="top",
            font=dict(size=17, color=theme.TEXT),
        ),
        autosize=True,
        height=theme.PLOT_HEIGHT,
        paper_bgcolor=theme.BACKGROUND,
        plot_bgcolor=theme.SURFACE,
        font=dict(family=theme.FONT_STACK, size=13, color=theme.TEXT),
        # The bottom margin has to clear the axis title *and* the wrapped
        # horizontal legend beneath it, or the two overlap on square plots.
        margin=dict(l=72, r=28, t=72, b=150),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.16,
            xanchor="center", x=0.5,
            font=dict(size=12, color=theme.TEXT),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
        hovermode="closest",
        xaxis=xaxis,
        yaxis=yaxis,
    )


# ---------------------------------------------------------------------------
# 1. McCabe-Thiele
# ---------------------------------------------------------------------------

def plot_xy(vle_data, col_result, z_F, composition_unit="mole fraction"):
    """McCabe-Thiele x-y diagram with equal axis scaling."""
    convert = lambda v: _convert(v, "composition", composition_unit)
    fig = go.Figure()
    axis_max = from_canonical(1.0, "composition", composition_unit)

    fig.add_trace(go.Scatter(
        x=convert(vle_data['x']), y=convert(vle_data['y']), mode='lines',
        name='Equilibrium curve', line=dict(color=theme.ACCENT, width=3),
        hovertemplate="x=%{x:.4g}<br>y=%{y:.4g}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0, axis_max], y=[0, axis_max], mode='lines', name='y = x',
        line=dict(color=theme.TEXT_FAINT, width=1.5, dash='dash'), hoverinfo='skip',
    ))

    x_az = from_canonical(vle_data['x_azeo'], "composition", composition_unit)
    fig.add_trace(go.Scatter(
        x=[x_az], y=[x_az], mode='markers',
        name=f'Azeotrope ({x_az:.3g})',
        marker=dict(symbol='diamond', size=12, color=theme.STAGE),
        hovertemplate="azeotrope x=y=%{x:.4g}<extra></extra>",
    ))

    mccabe = col_result.get('mccabe_lines', {})
    for key_x, key_y, name, color, dash in (
        ('rectifying_x', 'rectifying_y', 'Rectifying line', theme.ACCENT_DEEP, None),
        ('stripping_x', 'stripping_y', 'Stripping line', theme.STRIPPING, None),
        ('q_line_x', 'q_line_y', 'Feed q-line', theme.FEED, 'dash'),
    ):
        if key_x in mccabe:
            fig.add_trace(go.Scatter(
                x=convert(mccabe[key_x]), y=convert(mccabe[key_y]), mode='lines',
                name=name, line=dict(color=color, width=2.5, dash=dash),
            ))

    stair_x = mccabe.get('staircase_x', [])
    if len(stair_x) > 0:
        count = mccabe.get('stage_count', col_result['total_stages'])
        fig.add_trace(go.Scatter(
            x=convert(stair_x), y=convert(mccabe['staircase_y']), mode='lines',
            name=f"CMO staircase ({count} stages)",
            line=dict(color=theme.DANGER, width=2.5),
        ))

    xD = from_canonical(col_result['x_D'], "composition", composition_unit)
    xB = from_canonical(col_result['x_B'], "composition", composition_unit)
    zF = from_canonical(z_F, "composition", composition_unit)
    fig.add_trace(go.Scatter(
        x=[xD, zF, xB], y=[xD, zF, xB], mode='markers+text',
        name='Key compositions',
        marker=dict(size=10, color=theme.DIFFERENCE),
        text=['x_D', 'z_F', 'x_B'], textposition='top left',
        textfont=dict(size=14, color=theme.TEXT),
    ))

    fig.update_layout(**_layout(
        "McCabe-Thiele diagram (x-y)",
        f"Liquid IPA composition x ({composition_unit})",
        f"Vapour IPA composition y ({composition_unit})",
        x_range=(0.0, axis_max), square=True,
    ))
    return fig


# ---------------------------------------------------------------------------
# 2. Constant-pressure VLE
# ---------------------------------------------------------------------------

def plot_txy(vle_data, col_result, z_F, P, composition_unit="mole fraction",
             temperature_unit="°C"):
    """Constant-pressure T-x-y phase envelope."""
    convert = lambda v: _convert(v, "composition", composition_unit)
    x = convert(vle_data['x'])
    y = convert(vle_data['y'])
    T = _convert(vle_data['T_bubble_C'], "temperature", temperature_unit)
    axis_max = from_canonical(1.0, "composition", composition_unit)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=T, mode='lines', name='Bubble point (saturated liquid)',
        line=dict(color=theme.ACCENT, width=3),
        hovertemplate="x=%{x:.4g}<br>T=%{y:.4g}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=y, y=T, mode='lines', name='Dew point (saturated vapour)',
        line=dict(color=theme.VAPOR, width=3),
        hovertemplate="y=%{x:.4g}<br>T=%{y:.4g}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=np.concatenate([x, y[::-1]]), y=np.concatenate([T, T[::-1]]),
        fill='toself', fillcolor=theme.rgba(theme.ACCENT, 0.10),
        line=dict(width=0), name='Two-phase region',
        hoverinfo='skip',
    ))

    x_az = from_canonical(vle_data['x_azeo'], "composition", composition_unit)
    T_az = from_canonical(vle_data['T_azeo_C'], "temperature", temperature_unit)
    fig.add_trace(go.Scatter(
        x=[x_az], y=[T_az], mode='markers',
        name=f'Azeotrope ({x_az:.3g}, {T_az:.4g} {temperature_unit})',
        marker=dict(symbol='diamond', size=12, color=theme.STAGE),
    ))

    zF = from_canonical(z_F, "composition", composition_unit)
    fig.add_trace(go.Scatter(
        x=[zF, zF], y=[float(np.min(T)) - 5, float(np.max(T)) + 5], mode='lines',
        name=f'Feed z_F = {zF:.3g}',
        line=dict(color=theme.FEED, width=2, dash='dash'), hoverinfo='skip',
    ))

    fig.update_layout(**_layout(
        "Constant-pressure VLE (T-x-y)",
        f"IPA composition x, y ({composition_unit})",
        f"Temperature ({temperature_unit})",
        x_range=(0.0, axis_max),
    ))
    return fig


# ---------------------------------------------------------------------------
# 3. Ponchon-Savarit
# ---------------------------------------------------------------------------

def plot_ponchon_savarit(vle_data, col_result, z_F, h_F,
                         composition_unit="mole fraction", enthalpy_unit="kJ/mol"):
    """Enthalpy-composition diagram with tie lines, rays and difference points."""
    cx = lambda v: _convert(v, "composition", composition_unit)
    ch = lambda v: _convert(v, "enthalpy", enthalpy_unit)
    axis_max = from_canonical(1.0, "composition", composition_unit)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cx(vle_data['x']), y=ch(vle_data['h_L']), mode='lines',
        name='Saturated liquid h_L(x)', line=dict(color=theme.ACCENT, width=3),
    ))
    fig.add_trace(go.Scatter(
        x=cx(vle_data['y']), y=ch(vle_data['H_V']), mode='lines',
        name='Saturated vapour H_V(y)', line=dict(color=theme.VAPOR, width=3),
    ))

    # Tie lines, drawn as one trace with NaN separators instead of one per stage.
    stages = col_result['stages']
    tie_x, tie_y = [], []
    for s in stages:
        tie_x += [s['x'], s['y'], np.nan]
        tie_y += [s['h_L'], s['H_V'], np.nan]
    if tie_x:
        fig.add_trace(go.Scatter(
            x=cx(tie_x), y=ch(tie_y), mode='lines+markers',
            name=f'Equilibrium tie lines ({len(stages)})',
            line=dict(color=theme.STAGE, width=1.5),
            marker=dict(size=5, color=theme.STAGE_DEEP),
        ))

    # Construction rays, likewise grouped by section into a single trace each.
    rays = col_result.get('construction_lines', [])
    for ray_type, color in (('rectifying', theme.DIFFERENCE_SOFT),
                            ('stripping', theme.HEAT)):
        rx, ry = [], []
        for line in (r for r in rays if r.get('type') == ray_type):
            rx += [line['x0'], line['x1'], line.get('x2', line['x1']), np.nan]
            ry += [line['y0'], line['y1'], line.get('y2', line['y1']), np.nan]
        if rx:
            fig.add_trace(go.Scatter(
                x=cx(rx), y=ch(ry), mode='lines',
                name=f'{ray_type.capitalize()} operating rays',
                line=dict(color=color, width=1.5, dash='dot'),
            ))

    xD, QD = cx(col_result['x_D']), ch(col_result['Q_prime_D'])
    xB, QB = cx(col_result['x_B']), ch(col_result['Q_prime_B'])
    zF, hF = cx(z_F), ch(h_F)

    fig.add_trace(go.Scatter(
        x=[xD, zF, xB], y=[QD, hF, QB], mode='lines',
        name='Collinear Δ_D - F - Δ_B',
        line=dict(color=theme.STAGE, width=2, dash='dash'),
    ))
    for x_pt, y_pt, label, color, pos in (
        (xD, QD, 'Δ_D', theme.DIFFERENCE, 'top center'),
        (xB, QB, 'Δ_B', theme.ACCENT, 'bottom center'),
        (zF, hF, 'Feed', theme.FEED, 'middle right'),
    ):
        fig.add_trace(go.Scatter(
            x=[x_pt], y=[y_pt], mode='markers+text',
            name=f"{label} ({x_pt:.3g}, {y_pt:.4g})",
            marker=dict(size=13, color=color,
                        symbol='square' if label == 'Feed' else 'circle'),
            text=[label], textposition=pos,
            textfont=dict(size=14, color=color),
        ))

    fig.update_layout(**_layout(
        "Ponchon-Savarit diagram (H-x-y)",
        f"IPA composition x, y ({composition_unit})",
        f"Molar enthalpy ({enthalpy_unit})",
        x_range=(0.0, axis_max),
    ))
    return fig


# ---------------------------------------------------------------------------
# 4. Internal flow profiles
# ---------------------------------------------------------------------------

def plot_flow_profiles(col_result, flow_unit="mol/s"):
    """Stage-by-stage internal liquid and vapour flows, showing the feed jump."""
    stages = col_result['stages']
    stage_nums = np.array([s['stage'] for s in stages])
    L = _convert([s['L'] for s in stages], "flow", flow_unit)
    V = _convert([s['V'] for s in stages], "flow", flow_unit)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stage_nums, y=L, mode='lines+markers', name='Liquid L_n',
        line=dict(color=theme.ACCENT, width=3), marker=dict(size=9),
        hovertemplate="stage %{x}<br>L=%{y:.4g}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=stage_nums, y=V, mode='lines+markers', name='Vapour V_n',
        line=dict(color=theme.VAPOR, width=3), marker=dict(size=9),
        hovertemplate="stage %{x}<br>V=%{y:.4g}<extra></extra>",
    ))
    fig.add_vline(
        x=col_result['feed_stage'], line_width=2, line_dash="dash",
        line_color=theme.FEED,
        annotation_text=f"Feed stage ({col_result['feed_stage']})",
        annotation_position="top right",
        annotation_font=dict(size=13, color=theme.FEED),
    )

    layout = _layout(
        "Internal flows (non-CMO)",
        "Stage number (top = 1)",
        f"Molar flow ({flow_unit})",
    )
    layout["xaxis"]["dtick"] = 1
    fig.update_layout(**layout)
    return fig

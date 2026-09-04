"""Interactive Plotly Visualizations (Side Legends Outside Plot, 1:1 Aspect Ratio Axes):
1. McCabe-Thiele (x-y) Diagram with Staircase, Operating Lines, q-Line, 1:1 aspect ratio
2. Constant P VLE (T-x-y) Diagram (x in [0, 1])
3. Ponchon-Savarit (H-x-y) Diagram (x in [0, 1])
4. Stage-by-Stage Liquid & Vapor Flow Profiles (Non-CMO)
"""

import plotly.graph_objects as go
import numpy as np
from src.units import from_canonical

DARK_LAYOUT_BASE = dict(
    template="plotly_dark",
    width=680,
    height=520,
    paper_bgcolor="#0f172a",
    plot_bgcolor="#1e293b",
    font=dict(family="sans-serif", size=13, color="#f8fafc"),
    margin=dict(l=70, r=180, t=40, b=50),
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1.0,
        xanchor="left",
        x=1.02,
        font=dict(size=12, color="#f8fafc"),
        bgcolor="rgba(0, 0, 0, 0)",
        bordercolor="rgba(0, 0, 0, 0)"
    )
)

def plot_xy(vle_data, col_result, z_F, composition_unit="mole fraction"):
    """Generate McCabe-Thiele (x-y) Diagram with 1:1 aspect ratio axes and side legend."""
    fig = go.Figure()
    convert_x = lambda values: [from_canonical(v, "composition", composition_unit) for v in values]
    xs = convert_x(vle_data['x'])
    ys = convert_x(vle_data['y'])
    axis_max = from_canonical(1.0, "composition", composition_unit)
    
    # VLE Equilibrium Curve
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode='lines',
        name='VLE Curve',
        line=dict(color='#38bdf8', width=3)
    ))
    
    # y = x Diagonal
    fig.add_trace(go.Scatter(
        x=[0, axis_max], y=[0, axis_max],
        mode='lines',
        name='y = x',
        line=dict(color='#64748b', width=1.5, dash='dash')
    ))
    
    # Azeotrope
    x_az_raw = vle_data['x_azeo']
    x_az = from_canonical(x_az_raw, "composition", composition_unit)
    fig.add_trace(go.Scatter(
        x=[x_az], y=[x_az],
        mode='markers',
        name=f'Azeotrope ({x_az:.3g} {composition_unit})',
        marker=dict(symbol='diamond', size=12, color='#facc15')
    ))
    
    mccabe = col_result.get('mccabe_lines', {})
    
    # Rectifying Operating Line
    if 'rectifying_x' in mccabe:
        fig.add_trace(go.Scatter(
            x=convert_x(mccabe['rectifying_x']), y=convert_x(mccabe['rectifying_y']),
            mode='lines',
            name='Rectifying Line',
            line=dict(color='#06b6d4', width=2.5)
        ))
    
    # Stripping Operating Line
    if 'stripping_x' in mccabe:
        fig.add_trace(go.Scatter(
            x=convert_x(mccabe['stripping_x']), y=convert_x(mccabe['stripping_y']),
            mode='lines',
            name='Stripping Line',
            line=dict(color='#f97316', width=2.5)
        ))
    
    # Feed q-Line
    if 'q_line_x' in mccabe:
        fig.add_trace(go.Scatter(
            x=convert_x(mccabe['q_line_x']), y=convert_x(mccabe['q_line_y']),
            mode='lines',
            name='Feed q-Line',
            line=dict(color='#10b981', width=2.5, dash='dash')
        ))
    
    # Staircase Steps
    stair_x = mccabe.get('staircase_x', [])
    stair_y = mccabe.get('staircase_y', [])
    if len(stair_x) > 0:
        fig.add_trace(go.Scatter(
            x=convert_x(stair_x), y=convert_x(stair_y),
            mode='lines',
            name=f"Staircase ({col_result['total_stages']} Stages)",
            line=dict(color='#ef4444', width=2.5)
        ))
    
    # Product & Feed Points
    xD = from_canonical(col_result['x_D'], "composition", composition_unit)
    xB = from_canonical(col_result['x_B'], "composition", composition_unit)
    z_F = from_canonical(z_F, "composition", composition_unit)
    fig.add_trace(go.Scatter(
        x=[xD, z_F, xB], y=[xD, z_F, xB],
        mode='markers+text',
        name='x_B, z_F, x_D',
        marker=dict(size=10, color='#a855f7'),
        text=['x_D', 'z_F', 'x_B'],
        textposition='top left',
        textfont=dict(size=14, color="#f8fafc")
    ))

    fig.update_layout(
        **DARK_LAYOUT_BASE,
        xaxis=dict(
            title=dict(text=f"<b>Liquid IPA composition x ({composition_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            range=[0.0, axis_max],
            autorange=False,
            fixedrange=False,
            constrain="domain",
            gridcolor="#334155"
        ),
        yaxis=dict(
            title=dict(text=f"<b>Vapor IPA composition y ({composition_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            range=[0.0, axis_max],
            autorange=False,
            fixedrange=False,
            scaleanchor="x",
            scaleratio=1,
            constrain="domain",
            gridcolor="#334155"
        )
    )
    return fig

def plot_txy(vle_data, col_result, z_F, P, composition_unit="mole fraction", temperature_unit="°C"):
    """Generate Constant P VLE (T-x-y) Diagram with side legend."""
    fig = go.Figure()
    xs = [from_canonical(v, "composition", composition_unit) for v in vle_data['x']]
    T_C = [from_canonical(v, "temperature", temperature_unit) for v in vle_data['T_bubble_C']]
    ys = [from_canonical(v, "composition", composition_unit) for v in vle_data['y']]
    axis_max = from_canonical(1.0, "composition", composition_unit)
    
    fig.add_trace(go.Scatter(
        x=xs, y=T_C,
        mode='lines',
        name='Bubble Point',
        line=dict(color='#38bdf8', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=ys, y=T_C,
        mode='lines',
        name='Dew Point',
        line=dict(color='#f87171', width=3)
    ))
    
    x_az = from_canonical(vle_data['x_azeo'], "composition", composition_unit)
    T_az_C = from_canonical(vle_data['T_azeo_C'], "temperature", temperature_unit)
    fig.add_trace(go.Scatter(
        x=[x_az], y=[T_az_C],
        mode='markers',
        name=f'Azeotrope ({x_az:.3g} {composition_unit})',
        marker=dict(symbol='diamond', size=12, color='#facc15')
    ))
    
    z_F = from_canonical(z_F, "composition", composition_unit)
    fig.add_trace(go.Scatter(
        x=[z_F, z_F], y=[min(T_C) - 5, max(T_C) + 5],
        mode='lines',
        name=f'Feed (z_F={z_F:.2f})',
        line=dict(color='#10b981', width=2, dash='dash')
    ))
    
    fig.update_layout(
        **DARK_LAYOUT_BASE,
        xaxis=dict(
            title=dict(text=f"<b>Isopropanol composition x,y ({composition_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            range=[0.0, axis_max],
            autorange=False,
            fixedrange=False,
            constrain="domain",
            gridcolor="#334155"
        ),
        yaxis=dict(
            title=dict(text=f"<b>Temperature ({temperature_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            fixedrange=False,
            constrain="domain",
            gridcolor="#334155"
        )
    )
    return fig

def plot_ponchon_savarit(vle_data, col_result, z_F, h_F, composition_unit="mole fraction", enthalpy_unit="kJ/mol"):
    """Generate Ponchon-Savarit (H-x-y) Diagram (side legend, x in [0, 1])."""
    fig = go.Figure()
    cx = lambda value: from_canonical(value, "composition", composition_unit)
    ch = lambda value: from_canonical(value, "enthalpy", enthalpy_unit)
    xs = [cx(v) for v in vle_data['x']]
    h_L = [ch(v) for v in vle_data['h_L']]
    H_V = [ch(v) for v in vle_data['H_V']]
    axis_max = cx(1.0)
    
    fig.add_trace(go.Scatter(
        x=xs, y=h_L,
        mode='lines',
        name='Sat. Liquid h_L',
        line=dict(color='#38bdf8', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=xs, y=H_V,
        mode='lines',
        name='Sat. Vapor H_V',
        line=dict(color='#f87171', width=3)
    ))
    
    xD = cx(col_result['x_D'])
    Q_prime_D = ch(col_result['Q_prime_D'])
    xB = cx(col_result['x_B'])
    Q_prime_B = ch(col_result['Q_prime_B'])
    z_F, h_F = cx(z_F), ch(h_F)
    
    fig.add_trace(go.Scatter(
        x=[xD], y=[Q_prime_D],
        mode='markers+text',
        name=f"Δ_D ({xD:.2f}, {Q_prime_D:.1f})",
        marker=dict(symbol='circle', size=13, color='#a855f7'),
        text=[f"Δ_D"],
        textposition='top center',
        textfont=dict(size=14, color="#a855f7")
    ))
    
    fig.add_trace(go.Scatter(
        x=[xB], y=[Q_prime_B],
        mode='markers+text',
        name=f"Δ_B ({xB:.2f}, {Q_prime_B:.1f})",
        marker=dict(symbol='circle', size=13, color='#38bdf8'),
        text=[f"Δ_B"],
        textposition='bottom center',
        textfont=dict(size=14, color="#38bdf8")
    ))
    
    fig.add_trace(go.Scatter(
        x=[z_F], y=[h_F],
        mode='markers+text',
        name=f"Feed F ({z_F:.2f}, {h_F:.1f})",
        marker=dict(symbol='square', size=12, color='#10b981'),
        text=[f"Feed"],
        textposition='middle right',
        textfont=dict(size=14, color="#10b981")
    ))
    
    fig.add_trace(go.Scatter(
        x=[xD, z_F, xB], y=[Q_prime_D, h_F, Q_prime_B],
        mode='lines',
        name='Operating Line',
        line=dict(color='#facc15', width=2, dash='dash')
    ))
    
    for s in col_result['stages']:
        fig.add_trace(go.Scatter(
            x=[cx(s['x']), cx(s['y'])], y=[ch(s['h_L']), ch(s['H_V'])],
            mode='lines+markers',
            showlegend=False,
            line=dict(color='#facc15', width=1.5),
            marker=dict(size=5, color='#eab308')
        ))
    
    lines = col_result.get('construction_lines', [])
    for line in lines[:15]:
        fig.add_trace(go.Scatter(
            x=[cx(line['x0']), cx(line['x1'])], y=[ch(line['y0']), ch(line['y1'])],
            mode='lines',
            showlegend=False,
            line=dict(color='rgba(148, 163, 184, 0.3)', width=1, dash='dot')
        ))

    fig.update_layout(
        **DARK_LAYOUT_BASE,
        xaxis=dict(
            title=dict(text=f"<b>Isopropanol composition x,y ({composition_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            range=[0.0, axis_max],
            autorange=False,
            fixedrange=False,
            constrain="domain",
            gridcolor="#334155"
        ),
        yaxis=dict(
            title=dict(text=f"<b>Molar enthalpy ({enthalpy_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            fixedrange=False,
            gridcolor="#334155"
        )
    )
    return fig

def plot_flow_profiles(col_result, flow_unit="mol/s"):
    """Generate Stage-by-Stage Vapor and Liquid Flow Profiles (side legend)."""
    fig = go.Figure()
    stages = col_result['stages']
    stage_nums = [s['stage'] for s in stages]
    Ls = [from_canonical(s['L'], "flow", flow_unit) for s in stages]
    Vs = [from_canonical(s['V'], "flow", flow_unit) for s in stages]
    feed_stage = col_result['feed_stage']
    
    fig.add_trace(go.Scatter(
        x=stage_nums, y=Ls,
        mode='lines+markers',
        name='Liquid Flow (L_n)',
        line=dict(color='#38bdf8', width=3),
        marker=dict(size=9)
    ))
    
    fig.add_trace(go.Scatter(
        x=stage_nums, y=Vs,
        mode='lines+markers',
        name='Vapor Flow (V_n)',
        line=dict(color='#f87171', width=3),
        marker=dict(size=9)
    ))
    
    fig.add_vline(
        x=feed_stage,
        line_width=2,
        line_dash="dash",
        line_color="#10b981",
        annotation_text=f"Feed Stage ({feed_stage})",
        annotation_position="top right",
        annotation_font=dict(size=13, color="#10b981")
    )

    fig.update_layout(
        **DARK_LAYOUT_BASE,
        xaxis=dict(
            title=dict(text="<b>Stage Number (Top = 1, Bottom = N)</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            dtick=1,
            fixedrange=False,
            gridcolor="#334155"
        ),
        yaxis=dict(
            title=dict(text=f"<b>Flow rate ({flow_unit})</b>", font=dict(size=15, color="#e2e8f0")),
            tickfont=dict(size=13, color="#cbd5e1"),
            fixedrange=False,
            gridcolor="#334155"
        )
    )
    return fig

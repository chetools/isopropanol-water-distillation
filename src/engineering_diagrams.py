"""Responsive, publication-quality SVG diagrams used by the tutorial.

The drawings are generated as vector markup so labels remain sharp when the
browser is zoomed or the tutorial is printed.  No external assets are needed.
"""

from html import escape


def _start(title: str, subtitle: str, height: int) -> list[str]:
    return [f"""
<div style="margin:0.9rem 0 1.25rem 0; width:100%; overflow-x:auto">
<svg viewBox="0 0 1000 {height}" width="100%" role="img"
     aria-label="{escape(title)}" xmlns="http://www.w3.org/2000/svg"
     style="min-width:0;max-width:1180px;display:block;margin:auto;font-family:Inter,Segoe UI,Arial,sans-serif">
  <title>{escape(title)}</title><desc>{escape(subtitle)}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#111d35"/><stop offset="1" stop-color="#0b1324"/>
    </linearGradient>
    <linearGradient id="unit" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#263b5d"/><stop offset="1" stop-color="#172640"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#020617" flood-opacity="0.55"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8"/>
    </marker>
    <marker id="heat-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#fb923c"/>
    </marker>
    <marker id="green-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#34d399"/>
    </marker>
  </defs>
  <rect x="4" y="4" width="992" height="{height - 8}" rx="18" fill="url(#bg)" stroke="#334155"/>
  <text x="36" y="42" fill="#f8fafc" font-size="23" font-weight="700">{escape(title)}</text>
  <text x="36" y="68" fill="#94a3b8" font-size="14">{escape(subtitle)}</text>
"""]


def _finish(parts: list[str]) -> str:
    parts.append("</svg></div>")
    return "".join(parts)


def _node(x: int, y: int, w: int, h: int, title: str, subtitle: str = "", accent: str = "#38bdf8") -> str:
    title_y = y + h / 2 - (7 if subtitle else -5)
    subtitle_markup = (
        f'<text x="{x + w / 2}" y="{title_y + 24}" text-anchor="middle" fill="#a9b8cc" font-size="13">{escape(subtitle)}</text>'
        if subtitle else ""
    )
    return f"""
  <g filter="url(#shadow)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="url(#unit)" stroke="{accent}" stroke-width="1.6"/>
    <rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{accent}"/>
    <text x="{x + w / 2}" y="{title_y}" text-anchor="middle" fill="#f8fafc" font-size="16" font-weight="700">{escape(title)}</text>
    {subtitle_markup}
  </g>"""


def _stream(x1: int, y1: int, x2: int, y2: int, label: str, detail: str = "", heat: bool = False, green: bool = False) -> str:
    color = "#fb923c" if heat else ("#34d399" if green else "#38bdf8")
    marker = "heat-arrow" if heat else ("green-arrow" if green else "arrow")
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    label_y = my - 10 if abs(x2 - x1) >= abs(y2 - y1) else my
    anchor = "middle" if abs(x2 - x1) >= abs(y2 - y1) else ("start" if mx < 500 else "end")
    dx = 0 if anchor == "middle" else (12 if anchor == "start" else -12)
    detail_markup = f'<text x="{mx + dx}" y="{label_y + 18}" text-anchor="{anchor}" fill="#94a3b8" font-size="12">{escape(detail)}</text>' if detail else ""
    return f"""
  <path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{color}" stroke-width="3" marker-end="url(#{marker})"/>
  <text x="{mx + dx}" y="{label_y}" text-anchor="{anchor}" fill="{color}" font-size="14" font-weight="700">{escape(label)}</text>
  {detail_markup}"""


def _equation_box(x: int, y: int, w: int, lines: list[str]) -> str:
    h = 28 + 23 * len(lines)
    text = "".join(
        f'<text x="{x + 16}" y="{y + 28 + 22 * i}" fill="{("#f8fafc" if i == 0 else "#cbd5e1")}" font-size="{("14" if i == 0 else "13")}" font-weight="{("700" if i == 0 else "400")}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#0f1a2e" stroke="#475569"/>{text}'


def whole_column_balance_svg() -> str:
    p = _start("Whole-column material and energy balance envelope", "Arrows define the sign convention used in the derivation", 510)
    p.append('<rect x="245" y="92" width="510" height="310" rx="24" fill="#0f2138" fill-opacity="0.36" stroke="#64748b" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append('<text x="270" y="120" fill="#94a3b8" font-size="13" font-weight="700">CONTROL VOLUME</text>')
    p.append(_node(390, 130, 220, 62, "TOTAL CONDENSER", "vapor → liquid"))
    p.append(_node(390, 224, 220, 76, "TRAY COLUMN", "N equilibrium stages", "#a78bfa"))
    p.append(_node(390, 332, 220, 62, "PARTIAL REBOILER", "liquid ⇌ vapor", "#34d399"))
    p.append(_stream(390, 171, 610, 171, "internal reflux", "L₀, xᴅ, hᴿ", green=True))
    p.append(_stream(610, 254, 390, 254, "internal vapor", "V₁, y₁, H₁"))
    p.append(_stream(55, 262, 390, 262, "FEED", "F, zꜰ, hꜰ"))
    p.append(_stream(610, 151, 925, 151, "DISTILLATE", "D, xᴅ, hᴅ"))
    p.append(_stream(610, 371, 925, 371, "BOTTOMS", "B, xʙ, hʙ"))
    p.append(_stream(500, 82, 500, 130, "Qᴄ out", "positive magnitude", heat=True))
    p.append(_stream(500, 458, 500, 394, "Qʀ in", "positive magnitude", heat=True))
    p.append(_equation_box(45, 414, 395, ["Independent steady-state balances", "Total: F = D + B", "IPA: F zꜰ = D xᴅ + B xʙ"]))
    p.append(_equation_box(560, 414, 395, ["Energy on one common reference", "F hꜰ + Qʀ = D hᴅ + B hʙ + Qᴄ", "No accumulation, reaction, or heat loss"]))
    return _finish(p)


def model_map_svg() -> str:
    p = _start("From specifications to a buildable column", "Information flow and the calculation boundary between process and equipment design", 420)
    nodes = [
        (45, 125, "FEED + SPECS", "F, zꜰ, hꜰ, P; xᴅ, xʙ, R", "#38bdf8"),
        (275, 125, "THERMODYNAMICS", "γ-NRTL, Pˢᵃᵗ, h, H", "#a78bfa"),
        (505, 125, "STAGE SOLVER", "MESH + difference points", "#34d399"),
        (735, 125, "PROCESS RESULTS", "N, feed tray, Lₙ, Vₙ, Qᴄ, Qʀ", "#fbbf24"),
        (505, 270, "EQUIPMENT DESIGN", "hydraulics, shell, exchangers", "#fb923c"),
        (735, 270, "COST + SAFETY", "TAC, operability, safeguards", "#f43f5e"),
    ]
    for x, y, title, sub, color in nodes:
        p.append(_node(x, y, 205, 82, title, sub, color))
    for x in (250, 480, 710):
        p.append(f'<path d="M{x} 166 L{x + 25} 166" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>')
    p.append('<path d="M837 207 C837 245 710 250 710 270" stroke="#64748b" stroke-width="3" fill="none" marker-end="url(#arrow)"/>')
    p.append('<path d="M710 311 L735 311" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>')
    p.append(_equation_box(45, 255, 400, ["Always close the balances first", "F=D+B; Fzꜰ=Dxᴅ+Bxʙ", "Fhꜰ+Qʀ=Dhᴅ+Bhʙ+Qᴄ"]))
    return _finish(p)


def azeotrope_svg() -> str:
    p = _start("Azeotrope and relative-volatility diagnostic", "A crossing of y(x) with the diagonal removes the ordinary-distillation driving force", 410)
    p.append('<path d="M100 325 L100 105 M100 325 L535 325" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>')
    p.append('<text x="82" y="102" fill="#cbd5e1" font-size="14">yIPA</text><text x="510" y="350" fill="#cbd5e1" font-size="14">xIPA</text>')
    p.append('<path d="M100 325 L510 115" stroke="#64748b" stroke-width="2" stroke-dasharray="7 6"/>')
    p.append('<path d="M100 325 C210 160 330 125 385 184 C430 230 475 162 510 115" fill="none" stroke="#38bdf8" stroke-width="4"/>')
    p.append('<circle cx="385" cy="184" r="7" fill="#fb923c" stroke="#fff7ed" stroke-width="2"/>')
    p.append('<path d="M385 184 L385 325" stroke="#fb923c" stroke-width="2" stroke-dasharray="5 5"/>')
    p.append('<text x="395" y="174" fill="#fb923c" font-size="14" font-weight="700">y = x; α₁₂ = 1</text>')
    p.append('<text x="218" y="178" fill="#38bdf8" font-size="14">α₁₂ &gt; 1: IPA enriches in vapor</text>')
    p.append('<text x="405" y="270" fill="#a9b8cc" font-size="13">α₁₂ &lt; 1</text>')
    p.append(_equation_box(585, 105, 360, ["Relative volatility", "α₁₂=(y₁/x₁)/(y₂/x₂)", "α₁₂=1 ⇒ y₁=x₁", "Driving force y₁−x₁ vanishes"]))
    p.append(_equation_box(585, 245, 360, ["Numerical root", "r(x)=y₁(x,P)−x", "Bracket each branch; do not step across", "the fixed-pressure azeotrope."]))
    return _finish(p)


def flash_balance_svg() -> str:
    p = _start("Single equilibrium-flash balance envelope", "One feed splits into coexisting liquid and vapor phases", 430)
    p.append('<rect x="235" y="92" width="530" height="250" rx="24" fill="#0f2138" fill-opacity="0.36" stroke="#64748b" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append('<path d="M420 145 Q500 105 580 145 L580 285 Q500 325 420 285 Z" fill="url(#unit)" stroke="#38bdf8" stroke-width="2" filter="url(#shadow)"/>')
    p.append('<path d="M424 220 Q500 250 576 220 L576 282 Q500 315 424 282 Z" fill="#164e63" fill-opacity="0.75"/>')
    p.append('<text x="500" y="190" text-anchor="middle" fill="#f8fafc" font-size="18" font-weight="700">FLASH DRUM</text>')
    p.append('<text x="500" y="214" text-anchor="middle" fill="#a9b8cc" font-size="13">T, P; yᵢ = Kᵢxᵢ</text>')
    p.append(_stream(55, 215, 420, 215, "FEED", "F, zᵢ, hꜰ"))
    p.append(_stream(580, 163, 925, 112, "VAPOR", "V = βF, yᵢ, H"))
    p.append(_stream(580, 270, 925, 320, "LIQUID", "L = (1−β)F, xᵢ, h", green=True))
    p.append(_stream(500, 77, 500, 145, "Q into flash", "Q = 0 if adiabatic", heat=True))
    p.append(_equation_box(70, 354, 390, ["Material closure", "F = L + V", "zᵢ = (1−β)xᵢ + βyᵢ"]))
    p.append(_equation_box(540, 354, 390, ["Energy closure", "hꜰ + Q/F = (1−β)h + βH", "β is restricted to 0 ≤ β ≤ 1"]))
    return _finish(p)


def flash_algorithm_svg() -> str:
    p = _start("Nested non-ideal adiabatic-flash algorithm", "The inner material/equilibrium solve must converge at every outer enthalpy trial", 465)
    nodes = [
        (55, 120, "BRACKET T", "Tlow, Thigh", "#38bdf8"),
        (275, 120, "NRTL K-VALUES", "Kᵢ=γᵢPᵢˢᵃᵗ/P", "#a78bfa"),
        (505, 120, "RACHFORD–RICE", "root β in [0,1]", "#34d399"),
        (735, 120, "UPDATE x, y, γ", "iterate to tolerance", "#fbbf24"),
        (505, 270, "ENTHALPY RESIDUAL", "rH=hꜰ−[(1−β)h+βH]", "#fb923c"),
        (735, 270, "CONVERGED STATE", "T, β, x, y, h, H", "#f43f5e"),
    ]
    for x, y, title, sub, color in nodes:
        p.append(_node(x, y, 205, 78, title, sub, color))
    for x in (260, 480, 710):
        p.append(f'<path d="M{x} 159 L{x + 15} 159" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>')
    p.append('<path d="M837 198 C837 245 650 230 620 270" stroke="#64748b" stroke-width="3" fill="none" marker-end="url(#arrow)"/>')
    p.append('<path d="M710 309 L735 309" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>')
    p.append('<path d="M505 309 C390 400 140 395 140 198" stroke="#fb923c" stroke-width="2.5" fill="none" stroke-dasharray="8 6" marker-end="url(#heat-arrow)"/>')
    p.append('<text x="280" y="395" fill="#fb923c" font-size="13" font-weight="700">outer bracketed T update while |rH| &gt; tolerance</text>')
    p.append('<path d="M835 120 C835 85 610 82 610 120" stroke="#a78bfa" stroke-width="2.5" fill="none" stroke-dasharray="7 5" marker-end="url(#arrow)"/>')
    p.append('<text x="720" y="78" text-anchor="middle" fill="#a78bfa" font-size="12">inner γ-composition iteration</text>')
    return _finish(p)


def mccabe_balance_svg() -> str:
    p = _start("McCabe–Thiele section envelopes", "The operating-line slope and intercept follow from these stream balances", 505)
    p.append('<line x1="500" y1="88" x2="500" y2="472" stroke="#334155" stroke-width="2"/>')
    p.append('<text x="250" y="112" text-anchor="middle" fill="#38bdf8" font-size="17" font-weight="700">RECTIFYING SECTION</text>')
    p.append('<text x="750" y="112" text-anchor="middle" fill="#34d399" font-size="17" font-weight="700">STRIPPING SECTION</text>')
    p.append('<rect x="120" y="145" width="260" height="180" rx="20" fill="#0f2138" fill-opacity="0.45" stroke="#64748b" stroke-width="2" stroke-dasharray="8 6"/>')
    p.append(_node(178, 195, 144, 78, "TRAYS 1…n", "upper envelope"))
    p.append(_stream(250, 355, 250, 273, "V, yₙ₊₁", "enters from below"))
    p.append(_stream(180, 195, 180, 126, "L, xₙ", "leaves downward", green=True))
    p.append(_stream(322, 220, 445, 220, "D, xᴅ", "product"))
    p.append('<rect x="620" y="145" width="260" height="180" rx="20" fill="#0f2138" fill-opacity="0.45" stroke="#64748b" stroke-width="2" stroke-dasharray="8 6"/>')
    p.append(_node(678, 195, 144, 78, "TRAYS m…N", "lower envelope", "#34d399"))
    p.append(_stream(750, 126, 750, 195, "L̅, xₘ", "enters from above", green=True))
    p.append(_stream(750, 273, 750, 355, "V̅, yₘ₊₁", "leaves upward"))
    p.append(_stream(822, 246, 945, 246, "B, xʙ", "product"))
    p.append(_equation_box(55, 375, 400, ["Rectifying balance", "V = L + D;  Vyₙ₊₁ = Lxₙ + Dxᴅ", "yₙ₊₁ = [R/(R+1)]xₙ + xᴅ/(R+1)"]))
    p.append(_equation_box(545, 375, 400, ["Stripping balance", "L̅ = V̅ + B;  L̅xₘ = V̅yₘ₊₁ + Bxʙ", "yₘ₊₁ = (L̅/V̅)xₘ − (B/V̅)xʙ"]))
    return _finish(p)


def mccabe_stagewalk_svg() -> str:
    p = _start("McCabe–Thiele ideal-stage construction", "Horizontal motion enforces equilibrium; vertical motion enforces the operating balance", 450)
    p.append('<path d="M95 365 L95 100 M95 365 L570 365" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>')
    p.append('<path d="M95 365 L545 115" stroke="#64748b" stroke-width="2" stroke-dasharray="7 6"/>')
    p.append('<path d="M95 365 C190 205 360 125 545 115" fill="none" stroke="#38bdf8" stroke-width="4"/>')
    p.append('<path d="M115 345 L545 125" fill="none" stroke="#34d399" stroke-width="3"/>')
    p.append('<path d="M505 145 L420 145 L420 190 L330 190 L330 242 L235 242 L235 295 L145 295" fill="none" stroke="#fb923c" stroke-width="3.5"/>')
    p.append('<text x="385" y="111" fill="#38bdf8" font-size="13">equilibrium curve y*=f(x)</text>')
    p.append('<text x="290" y="300" fill="#34d399" font-size="13">operating line</text>')
    p.append('<text x="555" y="385" fill="#cbd5e1" font-size="14">x</text><text x="72" y="98" fill="#cbd5e1" font-size="14">y</text>')
    p.append(_equation_box(620, 105, 325, ["One ideal stage", "1. horizontal: y fixed → equilibrium x", "2. vertical: x fixed → operating y", "3. repeat; switch line at q-line", "4. fractional last step is interpolated"]))
    p.append(_equation_box(620, 270, 325, ["Interpretation", "Total reflux: operating line → y=x", "Minimum reflux: pinch; N → ∞", "Real trays: apply verified efficiency"]))
    return _finish(p)


def mesh_stage_svg() -> str:
    p = _start("One equilibrium stage: complete MESH envelope", "Every stage must close material, equilibrium, summation, and enthalpy equations", 500)
    p.append('<rect x="170" y="110" width="420" height="230" rx="24" fill="#0f2138" fill-opacity="0.40" stroke="#64748b" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append(_node(300, 184, 170, 82, "STAGE n", "Tₙ, Pₙ; equilibrium", "#a78bfa"))
    p.append(_stream(65, 145, 300, 205, "Lₙ₋₁ enters", "xₙ₋₁, hₙ₋₁", green=True))
    p.append(_stream(65, 315, 300, 245, "Vₙ₊₁ enters", "yₙ₊₁, Hₙ₊₁"))
    p.append(_stream(470, 205, 695, 145, "Vₙ leaves", "yₙ, Hₙ"))
    p.append(_stream(470, 245, 695, 315, "Lₙ leaves", "xₙ, hₙ", green=True))
    p.append(_equation_box(625, 110, 330, ["M — component balance", "Lₙ₋₁xₙ₋₁ + Vₙ₊₁yₙ₊₁", "= Lₙxₙ + Vₙyₙ"]))
    p.append(_equation_box(625, 226, 330, ["E, S, H closures", "yᵢ = Kᵢ(T,P,x)xᵢ; Σxᵢ=Σyᵢ=1", "Lₙ₋₁hₙ₋₁ + Vₙ₊₁Hₙ₊₁", "= Lₙhₙ + VₙHₙ"]))
    p.append(_equation_box(55, 375, 515, ["Total balance", "Lₙ₋₁ + Vₙ₊₁ = Lₙ + Vₙ", "Residuals must be checked stage-by-stage—not only globally."]))
    return _finish(p)


def ponchon_stagewalk_svg() -> str:
    p = _start("Ponchon–Savarit enthalpy–composition stage walk", "Tie-lines impose equilibrium; rays through difference points impose material and energy balance", 490)
    p.append('<path d="M90 390 L90 95 M90 390 L610 390" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>')
    p.append('<path d="M105 330 C220 285 390 265 565 245" fill="none" stroke="#34d399" stroke-width="4"/>')
    p.append('<path d="M110 185 C240 125 400 130 570 175" fill="none" stroke="#38bdf8" stroke-width="4"/>')
    p.append('<line x1="185" y1="155" x2="185" y2="305" stroke="#a78bfa" stroke-width="2" stroke-dasharray="7 5"/>')
    p.append('<line x1="315" y1="136" x2="315" y2="275" stroke="#a78bfa" stroke-width="2" stroke-dasharray="7 5"/>')
    p.append('<line x1="448" y1="146" x2="448" y2="255" stroke="#a78bfa" stroke-width="2" stroke-dasharray="7 5"/>')
    p.append('<circle cx="570" cy="88" r="7" fill="#fb923c"/><text x="582" y="93" fill="#fb923c" font-size="15" font-weight="700">Δᴅ</text>')
    p.append('<circle cx="120" cy="365" r="7" fill="#f43f5e"/><text x="132" y="370" fill="#f43f5e" font-size="15" font-weight="700">Δʙ</text>')
    p.append('<path d="M570 88 L448 255 L315 136 L185 305" fill="none" stroke="#fb923c" stroke-width="2.8"/>')
    p.append('<path d="M185 305 L120 365" fill="none" stroke="#f43f5e" stroke-width="2.8"/>')
    p.append('<text x="395" y="118" fill="#38bdf8" font-size="13">saturated vapor H(y)</text>')
    p.append('<text x="390" y="294" fill="#34d399" font-size="13">saturated liquid h(x)</text>')
    p.append('<text x="616" y="410" fill="#cbd5e1" font-size="14">IPA mole fraction</text><text x="55" y="92" fill="#cbd5e1" font-size="14">H, h</text>')
    p.append(_equation_box(650, 100, 305, ["Rectifying difference point", "hΔD = hᴅ + Qᴄ/D", "V−L=D", "all upper rays pass through Δᴅ"]))
    p.append(_equation_box(650, 235, 305, ["Stripping difference point", "hΔB = hʙ − Qʀ/B", "L−V=B", "all lower rays pass through Δʙ"]))
    p.append(_equation_box(650, 370, 305, ["Closure check", "Δᴅ, feed point, and Δʙ collinear", "on a common enthalpy reference"]))
    return _finish(p)


def sizing_workflow_svg() -> str:
    p = _start("Auditable sizing and economics calculation chain", "Each box maps to a row in the dashboard calculation ledger", 560)
    boxes = [
        (55, 112, "SIMULATION LOADS", "max V, T, x, y, P; Qᴄ, Qʀ", "#38bdf8"),
        (375, 112, "PHASE PROPERTIES", "MWᵥ, ρᵥ, ρʟ, volumetric V", "#a78bfa"),
        (695, 112, "TRAY HYDRAULICS", "uꜰ, udesign, active + total area", "#34d399"),
        (695, 245, "COLUMN DIAMETER", "D = √(4A/π)", "#34d399"),
        (375, 245, "HEIGHT + SHELL", "tray stack, allowances, t, mass", "#fbbf24"),
        (55, 245, "HEAT EXCHANGERS", "A = |Q|/(U ΔTlm)", "#fb923c"),
        (55, 378, "BARE EQUIPMENT", "shell + trays + C + R", "#fb923c"),
        (375, 378, "FIXED CAPITAL", "index × material × install × scope", "#f43f5e"),
        (695, 378, "ANNUAL OPEX", "steam + cooling + maintenance", "#f43f5e"),
        (375, 486, "TOTAL ANNUALIZED COST", "TAC = CRF·FCI + OPEX", "#e879f9"),
    ]
    for x, y, title, sub, color in boxes:
        p.append(_node(x, y, 250, 72, title, sub, color))
    arrows = [
        (305, 148, 375, 148), (625, 148, 695, 148), (820, 184, 820, 245),
        (695, 281, 625, 281), (375, 281, 305, 281), (180, 317, 180, 378),
        (305, 414, 375, 414), (625, 414, 695, 414), (820, 450, 625, 510),
        (500, 450, 500, 486),
    ]
    for x1, y1, x2, y2 in arrows:
        p.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#64748b" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>')
    return _finish(p)


def safety_layers_svg() -> str:
    p = _start("Upset propagation and independent protection layers", "Example: total loss of condenser cooling while reboiler heat continues", 445)
    nodes = [
        (45, 135, "INITIATING EVENT", "cooling-water loss", "#fb923c"),
        (245, 135, "PHYSICAL RESPONSE", "Qᴄ ↓; vapor + P ↑", "#fbbf24"),
        (445, 135, "BPCS + ALARM", "pressure control; operator", "#38bdf8"),
        (645, 135, "INDEPENDENT TRIP", "high-high P removes Qʀ", "#34d399"),
        (825, 135, "RELIEF", "last-resort containment", "#f43f5e"),
    ]
    for x, y, title, sub, color in nodes:
        p.append(_node(x, y, 150, 90, title, sub, color))
    for x in (195, 395, 595, 795):
        p.append(f'<path d="M{x} 180 L{x + 50} 180" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>')
    p.append(_equation_box(85, 275, 390, ["Dynamic energy inventory", "dU/dt = Fhꜰ + Qʀ − Dhᴅ − Bhʙ − Qᴄ", "Cooling loss makes dU/dt positive until heat is removed."]))
    p.append(_equation_box(525, 275, 390, ["Relief basis", "ṁrelief ≥ vapor generation − remaining outlets", "Each layer must be verified for independence and reliability."]))
    return _finish(p)

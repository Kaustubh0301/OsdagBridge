from osdagbridge.core.utils.common import (
    KEY_DD_HAS_OVERHANG,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_VED,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')

def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\vspace{-0.5em}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\vspace{0.5em}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


# Order and labels for the Section 5.5 utilization-ratio summary chart.
UR_SUMMARY_COMPONENTS = ("Steel Plate\nGirders", "Concrete Deck\nSlab", "Cross\nBracing", "End\nDiaphragms")


def compute_overall_ur_summary(bridge) -> dict:
    """Governing (maximum) utilization ratio per structural component.

    Reuses the same per_girder / deck_report_values / cross-bracing data
    that chap5.py's Table 5.22 (Overall Design Check Summary) is built
    from, grouped the same way the table groups its rows: girder checks
    (moment, shear, LTB, deflection, stress, fatigue) -> Steel Plate
    Girders; deck checks (flexure, punching/one-way shear, crack width)
    plus the per-girder transverse-shear-in-slab check -> Concrete Deck
    Slab; cross-bracing axial + slenderness checks -> Cross Bracing;
    end-diaphragm axial checks (only when it is configured as a bracing
    member, mirroring Table 5.22) -> End Diaphragms.

    Returns {component_name: float | None} (None = no data for that
    component), keyed by the labels in UR_SUMMARY_COMPONENTS.
    """
    pg = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def _girder_max(check_ids):
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best:
                        best = d
            for lc, ld in (gd.get("per_lc") or {}).items():
                if str(lc).lower().startswith("envelope"):
                    continue
                for chk in (ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best:
                            best = d
        return best

    girder_vals = [v for v in (
        _girder_max({1}), _girder_max({2}), _girder_max({5}),
        _girder_max({13, 14}), _girder_max({11}), _girder_max({8, 9}),
    ) if v is not None]

    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}
    deck_vals = []
    if deck_rpt:
        def _dkv(key):
            v = deck_rpt.get(key)
            try:
                return float(v) if v not in (None, "") else 0.0
            except (TypeError, ValueError):
                return 0.0

        for dem_key, cap_key in (
            (KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT),
            (KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP),
            (KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
            (KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
        ):
            cap = _dkv(cap_key)
            if cap > 0:
                deck_vals.append(_dkv(dem_key) / cap)
        if bool(deck_rpt.get(KEY_DD_HAS_OVERHANG)):
            cap = _dkv(KEY_DD_MU_OH)
            if cap > 0:
                deck_vals.append(_dkv(KEY_DD_M_ULS_OH) / cap)
        wk_limit = _dkv(KEY_DD_WK_LIMIT)
        if wk_limit > 0:
            gov_wk = max(_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP), _dkv(KEY_DD_WK_OH))
            deck_vals.append(gov_wk / wk_limit)
    transverse_shear = _girder_max({16})
    if transverse_shear is not None:
        deck_vals.append(transverse_shear)

    cb_pairs = bridge.get_cb_pairs()

    def _cb_max(force_type):
        best = None
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                try:
                    ur = float(bridge.get_cb_efficiency(pair, member, force_type))
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best:
                    best = ur
        return best

    def _cb_slender_max():
        best = None
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                try:
                    sf = float(bridge.get_cb_slenderness(pair, member))
                except (TypeError, ValueError):
                    continue
                limit = 400.0 if member == "chord" else 250.0
                ratio = sf / limit
                if best is None or ratio > best:
                    best = ratio
        return best

    cb_vals = [v for v in (_cb_max("compression"), _cb_max("tension"), _cb_slender_max()) if v is not None]

    ed_type = ""
    for k, v in bridge.input_dict.items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
    ed_is_cb = "brac" in ed_type.strip().lower()
    ed_vals = [v for v in (_cb_max("compression"), _cb_max("tension")) if v is not None] if ed_is_cb else []

    values = [max(v) if v else None for v in (girder_vals, deck_vals, cb_vals, ed_vals)]
    return dict(zip(UR_SUMMARY_COMPONENTS, values))


def build_ur_summary_chart(ur_values: dict):
    """Render the Section 5.5 utilization-ratio bar chart to PNG bytes.

    One bar per component in UR_SUMMARY_COMPONENTS; a red dashed line marks
    the UR = 1.0 pass/fail threshold; passing bars (<= 1.0) use the brand
    green from report_theme, failing bars (> 1.0) use red. Components with
    no data (None) get no bar, just an "N/A" label. Returns None (caller
    shows a placeholder, same as other report figures) if every component
    is missing.
    """
    if all(v is None for v in ur_values.values()):
        return None

    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from osdagbridge.core.reports.report_theme import OSDAG_GREEN_HEX

    pass_color = "#" + OSDAG_GREEN_HEX
    fail_color = "#D32F2F"

    labels = list(UR_SUMMARY_COMPONENTS)
    values = [ur_values.get(lbl) for lbl in labels]
    x = range(len(labels))

    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    for i, v in enumerate(values):
        if v is None:
            ax.text(i, 0.03, "N/A", ha="center", va="bottom", fontsize=9, color="dimgray")
            continue
        ax.bar(i, v, width=0.55, color=(pass_color if v <= 1.0 else fail_color),
               edgecolor="black", linewidth=0.6)
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center", va="bottom", fontsize=9)

    ax.axhline(1.0, color="red", linestyle="--", linewidth=1.2)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Utilization Ratio")
    y_top = max([v for v in values if v is not None] + [1.0]) * 1.2
    ax.set_ylim(0, y_top)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()



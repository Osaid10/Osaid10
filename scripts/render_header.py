#!/usr/bin/env python3
"""Render the profile header banner as SVG, one file per colour scheme.

Both themes come from this one template so they can't drift apart. Everything
is plain SVG with CSS keyframes -- it renders as an <img> on GitHub, so there
is no JavaScript and no external font: the type stack falls back to whatever
the reader's OS provides.
"""

from pathlib import Path

W, H = 1000, 220

THEMES = {
    "dark": {
        "bg": "#0D1117", "panel": "#0F1621", "border": "#21262D",
        "text": "#E6EDF3", "muted": "#8B949E", "accent": "#00E5FF",
        "accent_soft": "#00E5FF", "glow": 0.16, "node_fill": "#0D1117",
        "live": "#3FB950", "edge": 0.18, "edge_live": 0.75, "node_w": 1.6,
    },
    "light": {
        "bg": "#FFFFFF", "panel": "#F6F8FA", "border": "#D0D7DE",
        "text": "#1F2328", "muted": "#59636E", "accent": "#0E7490",
        "accent_soft": "#22A0BD", "glow": 0.10, "node_fill": "#FFFFFF",
        "live": "#1A7F37", "edge": 0.34, "edge_live": 0.95, "node_w": 1.9,
    },
}

FONT = ("ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Roboto,Helvetica,Arial,sans-serif")
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")

# A 3-4-2 graph on the right. Coordinates only; edges are derived.
LAYERS = [
    [(742, 62), (742, 110), (742, 158)],
    [(846, 46), (846, 94), (846, 142), (846, 182)],
    [(946, 86), (946, 138)],
]


def edges() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    out = []
    for left, right in zip(LAYERS, LAYERS[1:]):
        for a in left:
            for b in right:
                out.append((a, b))
    return out


def render(theme: str) -> str:
    c = THEMES[theme]
    parts: list[str] = []

    # Edges. Every third one carries a travelling dash so the graph reads as
    # active without the whole thing flickering.
    for i, ((x1, y1), (x2, y2)) in enumerate(edges()):
        live = i % 3 == 0
        cls = "edge live" if live else "edge"
        delay = f' style="animation-delay:{(i % 7) * 0.45:.2f}s"' if live else ""
        parts.append(f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{delay}/>')

    # Nodes, pulsing on a stagger.
    for i, (x, y) in enumerate(p for layer in LAYERS for p in layer):
        parts.append(
            f'<circle class="node" cx="{x}" cy="{y}" r="5.5" '
            f'style="animation-delay:{i * 0.32:.2f}s"/>'
        )

    graph = "\n    ".join(parts)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="Osaid Khan Afridi, AI/ML Engineer">
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c['panel']}"/>
      <stop offset="1" stop-color="{c['bg']}"/>
    </linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{c['accent']}"/>
      <stop offset="1" stop-color="{c['accent']}" stop-opacity="0.15"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{c['accent']}" stop-opacity="{c['glow']}"/>
      <stop offset="1" stop-color="{c['accent']}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <style>
    .edge {{ stroke: {c['accent_soft']}; stroke-opacity: {c['edge']}; stroke-width: 1.1; }}
    .edge.live {{
      stroke-opacity: {c['edge_live']}; stroke-width: 1.4;
      stroke-dasharray: 5 95; stroke-dashoffset: 100;
      animation: flow 3.2s linear infinite;
    }}
    @keyframes flow {{ to {{ stroke-dashoffset: 0; }} }}

    .node {{
      fill: {c['node_fill']}; stroke: {c['accent']}; stroke-width: {c['node_w']};
      animation: pulse 3.6s ease-in-out infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ stroke-opacity: 0.45; }}
      50%      {{ stroke-opacity: 1; }}
    }}

    .live-dot {{ animation: blink 2.4s ease-in-out infinite; }}
    @keyframes blink {{
      0%, 100% {{ opacity: 1; }}
      50%      {{ opacity: 0.35; }}
    }}

    .caret {{ animation: caret 1.1s steps(1) infinite; }}
    @keyframes caret {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
  </style>

  <rect width="{W}" height="{H}" rx="14" fill="url(#panel)"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="13.5"
        fill="none" stroke="{c['border']}"/>
  <ellipse cx="860" cy="110" rx="260" ry="150" fill="url(#glow)"/>

  <g>
    {graph}
  </g>

  <rect x="44" y="50" width="3" height="104" rx="1.5" fill="url(#bar)"/>

  <text x="68" y="84" font-family="{FONT}" font-size="40" font-weight="700"
        letter-spacing="1.5" fill="{c['text']}">Osaid Khan Afridi</text>
  <text x="70" y="115" font-family="{MONO}" font-size="15" font-weight="600"
        letter-spacing="4.2" fill="{c['accent']}">AI / ML  ENGINEER</text>
  <text x="70" y="147" font-family="{FONT}" font-size="15"
        fill="{c['muted']}">Agentic systems, RAG and computer vision — shipped to production.</text>

  <g transform="translate(68, 170)">
    <rect width="404" height="30" rx="15" fill="{c['accent']}" fill-opacity="0.08"
          stroke="{c['accent']}" stroke-opacity="0.35"/>
    <circle class="live-dot" cx="18" cy="15" r="4" fill="{c['live']}"/>
    <text x="32" y="20" font-family="{MONO}" font-size="12.5" fill="{c['muted']}">
      open to full-time AI/ML roles · Pakistan &amp; remote<tspan class="caret"
      fill="{c['accent']}" dx="4">_</tspan></text>
  </g>
</svg>
"""


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for theme in THEMES:
        path = out / f"header-{theme}.svg"
        path.write_text(render(theme), encoding="utf-8")
        print(f"wrote {path.relative_to(path.parent.parent)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

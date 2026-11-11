"""Capa visual de RutaRentable (tema oscuro): CSS, logo, escena animada y fragmentos HTML.

No contiene lógica del modelo. Todo el HTML va en una sola línea para que Markdown no lo altere.
"""

FONDO, TARJETA, AMARILLO = "#11161C", "#1B232C", "#F5B800"
VERDE, AMBAR, ROJO = "#22C55E", "#F59E0B", "#EF4444"
TEXTO, TENUE = "#E8EDF2", "#93A1B0"
COLOR = {"verde": VERDE, "ambar": AMBAR, "rojo": ROJO}
RGB = {"verde": [34, 197, 94], "ambar": [245, 158, 11], "rojo": [239, 68, 68]}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');
:root{--fondo:#11161C;--tarjeta:#1B232C;--hundido:#141B22;--amarillo:#F5B800;--verde:#22C55E;--ambar:#F59E0B;--rojo:#EF4444;
 --texto:#E8EDF2;--tenue:#93A1B0;--borde:rgba(255,255,255,.06);--borde2:rgba(255,255,255,.13)}
html,body,.stApp,.stMarkdown,p,label,input,textarea,button,li{font-family:'Inter',system-ui,sans-serif}
h1,h2,h3,h4{font-family:'Sora','Inter',sans-serif !important;letter-spacing:-.01em}
.stApp{background:radial-gradient(1200px 500px at 80% -10%,rgba(245,184,0,.07),transparent 60%),var(--fondo)}
.block-container{padding-top:3.2rem;padding-bottom:1.5rem;max-width:1240px}
[data-testid="stHeader"]{background:transparent}

/* ---------- Escena: carretera de noche ---------- */
.rr-hero{position:relative;overflow:hidden;border-radius:22px;min-height:340px;color:var(--texto);margin-bottom:1rem;
 background:linear-gradient(180deg,#070B12 0%,#0E1A2B 48%,#1A2B42 78%,#24364F 100%);
 border:1px solid var(--borde);box-shadow:0 18px 40px rgba(0,0,0,.45)}
.rr-estrellas{position:absolute;inset:0;width:100%;height:70%;opacity:.8}
.rr-estrellas .t{animation:rr-titila 5s ease-in-out infinite alternate}
.rr-luna{position:absolute;right:7%;top:26px;width:46px;height:46px;border-radius:50%;background:#F4E9C1;
 box-shadow:0 0 34px 8px rgba(244,233,193,.22)}
.rr-montes{position:absolute;left:0;bottom:62px;width:200%;height:120px;will-change:transform}
.rr-montes svg{width:100%;height:100%;display:block}
.rr-montes.lejos{animation:rr-desliza 140s linear infinite}
.rr-montes.cerca{height:78px;animation:rr-desliza 60s linear infinite}
.rr-hero-txt{position:relative;z-index:3;padding:26px 30px 128px;max-width:720px}
.rr-marca{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.rr-marca svg{width:44px;height:44px;flex:none;filter:drop-shadow(0 4px 10px rgba(0,0,0,.4))}
.rr-nombre{font-family:'Sora',sans-serif;font-weight:800;font-size:1.25rem;line-height:1}
.rr-nombre span{color:var(--amarillo)}
.rr-nombre small{display:block;font-family:'Inter',sans-serif;font-weight:500;font-size:.72rem;color:var(--tenue);margin-top:4px;letter-spacing:.02em}
.rr-gancho{font-family:'Sora',sans-serif;font-weight:800;font-size:clamp(1.7rem,4.2vw,2.9rem);line-height:1.08;margin:0;
 animation:rr-entra .6s ease-out both}
.rr-gancho span{color:var(--amarillo)}
.rr-sub{font-size:clamp(.95rem,1.5vw,1.08rem);color:#C5D0DB;margin-top:10px;max-width:560px;line-height:1.45;
 animation:rr-entra .6s ease-out .12s both}
.rr-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;animation:rr-entra .6s ease-out .22s both}
.rr-chip{background:rgba(17,22,28,.55);border:1px solid var(--borde2);border-radius:999px;padding:5px 12px;font-size:.76rem;
 font-weight:600;color:#D5DEE7;white-space:nowrap;backdrop-filter:blur(4px)}
.rr-chip b{color:var(--amarillo);font-weight:700}
.rr-via{position:absolute;left:0;right:0;bottom:0;height:64px;z-index:1;
 background:linear-gradient(180deg,#2A323D 0%,#171D25 100%);border-top:2px solid rgba(245,184,0,.75)}
.rr-carril{position:absolute;left:0;right:0;bottom:22px;height:4px;opacity:.85;
 background:repeating-linear-gradient(90deg,#E8EDF2 0 38px,transparent 38px 84px);animation:rr-carril .9s linear infinite}
.rr-camion{position:absolute;z-index:2;bottom:26px;left:56%;width:190px;animation:rr-llega 1.6s cubic-bezier(.2,.7,.2,1) both}
.rr-camion svg{width:100%;height:auto;display:block;overflow:visible;animation:rr-bote .5s ease-in-out infinite alternate}
.rr-rueda{transform-box:fill-box;transform-origin:center;animation:rr-gira .7s linear infinite}
.rr-haz{animation:rr-haz 3.6s ease-in-out infinite alternate}
@keyframes rr-carril{to{background-position-x:-84px}}
@keyframes rr-desliza{to{transform:translateX(-50%)}}
@keyframes rr-llega{from{transform:translateX(-340px);opacity:0}to{transform:none;opacity:1}}
@keyframes rr-bote{from{transform:translateY(0)}to{transform:translateY(-1.5px)}}
@keyframes rr-gira{to{transform:rotate(360deg)}}
@keyframes rr-haz{from{opacity:.75}to{opacity:1}}
@keyframes rr-titila{from{opacity:.35}to{opacity:1}}
@keyframes rr-entra{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes rr-revela{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}
@keyframes rr-pulso{0%,100%{box-shadow:0 0 0 0 var(--halo),0 0 22px 2px var(--halo)}50%{box-shadow:0 0 0 9px transparent,0 0 30px 6px var(--halo)}}

/* ---------- Por qué RutaRentable ---------- */
.rr-porque{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:.2rem 0 1.1rem}
.rr-ben{display:flex;gap:12px;align-items:center;background:var(--tarjeta);border:1px solid var(--borde);border-radius:16px;
 padding:13px 15px;transition:transform .25s ease-out,border-color .25s ease-out}
.rr-ben:hover{transform:translateY(-3px);border-color:rgba(245,184,0,.45)}
.rr-ben .n{width:42px;height:42px;border-radius:12px;background:rgba(245,184,0,.12);display:grid;place-items:center;flex:none}
.rr-ben .n svg{width:23px;height:23px;color:var(--amarillo)}
.rr-ben b{display:block;font-family:'Sora',sans-serif;font-size:.95rem;color:var(--texto)}
.rr-ben span{font-size:.83rem;color:var(--tenue);line-height:1.35}

/* ---------- Tarjetas ---------- */
[class*="st-key-tarjeta_"]{background:var(--tarjeta);border:1px solid var(--borde) !important;border-radius:18px !important;
 box-shadow:0 10px 28px rgba(0,0,0,.35),0 0 0 1px rgba(245,184,0,.02);padding:1.1rem 1.2rem}
.st-key-tarjeta_resultado{border-top:3px solid var(--amarillo) !important}
.rr-titulo{display:flex;align-items:center;gap:10px;font-family:'Sora',sans-serif;font-weight:700;font-size:1.05rem;color:var(--texto);margin:0 0 .25rem}
.rr-titulo svg{width:21px;height:21px;flex:none;color:var(--amarillo)}
.stMarkdown p.rr-nota,.rr-nota{color:var(--tenue);font-size:.8rem !important;margin:0;line-height:1.4}
.rr-pista{display:flex;gap:8px;align-items:flex-start;font-size:.82rem;color:var(--tenue);line-height:1.4;margin:-.35rem 0 .35rem}
.rr-pista i{flex:none;width:8px;height:8px;border-radius:50%;margin-top:5px;background:var(--tenue)}
.rr-pista.ok i{background:var(--verde)}.rr-pista.est i{background:var(--ambar)}
.rr-pista b{color:#C9D3DD;font-weight:600}

/* ---------- Semáforo ---------- */
.rr-sem{--c:var(--verde);--halo:rgba(34,197,94,.45);display:flex;gap:18px;align-items:center;border-radius:18px;padding:18px 20px;
 background:linear-gradient(120deg,color-mix(in srgb,var(--c) 16%,#141B22),#141B22 70%);
 border:1px solid color-mix(in srgb,var(--c) 45%,transparent);animation:rr-revela .45s ease-out both}
.rr-sem.ambar{--c:var(--ambar);--halo:rgba(245,158,11,.45)}
.rr-sem.rojo{--c:var(--rojo);--halo:rgba(239,68,68,.45)}
.rr-luces{display:flex;flex-direction:column;gap:7px;background:#0B0F14;border:1px solid var(--borde2);border-radius:16px;padding:9px;flex:none}
.rr-luces i{width:26px;height:26px;border-radius:50%;background:#2A323D;display:block}
.rr-luces i.on{background:var(--c);animation:rr-pulso 2.6s ease-in-out infinite}
.rr-sem .t1{font-family:'Sora',sans-serif;font-weight:800;font-size:clamp(1.2rem,2.4vw,1.65rem);line-height:1.15;color:var(--c)}
.rr-sem .t2{font-size:clamp(.98rem,1.5vw,1.12rem);color:var(--texto);margin-top:7px;line-height:1.4}
.rr-sem .t2 b{color:var(--c);font-size:1.25em;font-family:'Sora',sans-serif}
.rr-picto{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px}
.rr-picto svg{width:34px;height:22px;animation:rr-entra .35s ease-out both}
.rr-picto .m{color:var(--rojo)}.rr-picto .b{color:var(--verde)}
.rr-picto-ley{font-size:.76rem;color:var(--tenue);margin-top:6px}
.rr-picto-ley i{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 5px 0 0}

/* ---------- Factores, odds, KPI ---------- */
.rr-fact{display:flex;flex-direction:column;gap:8px;margin:.3rem 0 .2rem}
.rr-fact div{display:flex;gap:10px;align-items:flex-start;background:var(--hundido);border:1px solid var(--borde);border-left:4px solid var(--tenue);
 border-radius:12px;padding:10px 13px;font-size:.9rem;line-height:1.45;color:#D5DEE7;animation:rr-entra .4s ease-out both}
.rr-fact div.sube{border-left-color:var(--rojo)}.rr-fact div.baja{border-left-color:var(--verde)}.rr-fact div.medio{border-left-color:var(--ambar)}
.rr-fact em{font-style:normal;font-weight:700;font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;white-space:nowrap;margin-top:3px;color:var(--tenue)}
.rr-fact .sube em{color:#FCA5A5}.rr-fact .baja em{color:#86EFAC}.rr-fact .medio em{color:#FCD34D}
.rr-odds{margin:10px 0 0;font-size:.8rem;color:var(--tenue);line-height:1.4}
.rr-odds b{color:#C9D3DD}
.rr-kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}
.rr-kpi{border:1px solid var(--borde);border-radius:14px;padding:11px 13px;background:var(--hundido)}
.rr-kpi .k{display:flex;align-items:center;gap:6px;font-size:.7rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--tenue);white-space:nowrap}
.rr-kpi .k svg{width:15px;height:15px;color:var(--amarillo)}
.rr-kpi .v{font-family:'Sora',sans-serif;font-weight:800;font-size:clamp(1rem,1.6vw,1.3rem);color:var(--texto);line-height:1.25;margin-top:2px}
.rr-kpi .s{font-size:.75rem;color:var(--tenue)}
.rr-leyenda{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;font-size:.76rem;color:var(--tenue);margin-top:-8px}
.rr-leyenda i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}

/* ---------- Comparador ---------- */
.rr-rank{display:flex;flex-direction:column;gap:10px;margin-top:.5rem}
.rr-of{--c:var(--verde);display:grid;grid-template-columns:44px 1fr auto;gap:14px;align-items:center;background:var(--hundido);
 border:1px solid var(--borde);border-left:5px solid var(--c);border-radius:14px;padding:12px 15px;animation:rr-entra .4s ease-out both}
.rr-of.ambar{--c:var(--ambar)}.rr-of.rojo{--c:var(--rojo)}
.rr-of.mejor{border-color:rgba(245,184,0,.6);border-left-color:var(--c);box-shadow:0 0 0 1px rgba(245,184,0,.25),0 8px 24px rgba(245,184,0,.08)}
.rr-of .pos{font-family:'Sora',sans-serif;font-weight:800;font-size:1.35rem;color:var(--tenue);text-align:center}
.rr-of.mejor .pos{color:var(--amarillo)}
.rr-of .r{font-family:'Sora',sans-serif;font-weight:700;font-size:1rem;color:var(--texto)}
.rr-of .d{font-size:.82rem;color:var(--tenue);margin-top:2px;line-height:1.4}
.rr-of .f{font-size:.88rem;color:#D5DEE7;margin-top:4px}
.rr-pastilla{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 12px;font-size:.78rem;font-weight:700;white-space:nowrap;
 color:var(--c);background:color-mix(in srgb,var(--c) 14%,transparent);border:1px solid color-mix(in srgb,var(--c) 45%,transparent)}
.rr-pastilla i{width:8px;height:8px;border-radius:50%;background:var(--c)}
.rr-sello{display:inline-block;margin-left:8px;border-radius:6px;padding:2px 8px;font-size:.68rem;font-weight:800;letter-spacing:.05em;
 text-transform:uppercase;background:var(--amarillo);color:#11161C;vertical-align:2px}
.rr-umbral{display:inline-flex;align-items:baseline;gap:10px;border:1px solid rgba(245,184,0,.4);background:rgba(245,184,0,.08);border-radius:12px;padding:8px 14px;margin:.2rem 0 .4rem}
.rr-umbral .k{font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--tenue);font-weight:700}
.rr-umbral .v{font-family:'Sora',sans-serif;font-weight:800;font-size:1.3rem;color:var(--amarillo)}

/* ---------- Widgets nativos en oscuro ---------- */
[data-testid="stWidgetLabel"] p{font-weight:600;color:#D5DEE7}
[data-baseweb="select"]>div,[data-baseweb="input"],[data-baseweb="base-input"],[data-testid="stNumberInputContainer"]{
 background-color:var(--hundido) !important;border-color:var(--borde2) !important;border-radius:12px !important}
[data-baseweb="input"] input,[data-baseweb="base-input"] input{color:var(--texto) !important;background:transparent !important}
[data-testid="stNumberInputContainer"] button{background:transparent !important;color:var(--tenue) !important}
[data-testid="stNumberInputContainer"] button:hover{color:var(--amarillo) !important}
[data-baseweb="select"]>div:focus-within,[data-testid="stNumberInputContainer"]:focus-within{border-color:var(--amarillo) !important}
[data-baseweb="popover"] ul,[data-baseweb="menu"]{background:#1F2832 !important}
.stButton button,.stDownloadButton button{border-radius:999px;border:1px solid var(--borde2);background:#222C37;color:var(--texto);
 font-weight:600;transition:border-color .2s ease-out,color .2s ease-out,transform .2s ease-out,background .2s ease-out}
.stButton button:hover,.stDownloadButton button:hover{border-color:var(--amarillo);color:var(--amarillo);transform:translateY(-1px)}
.stButton button[kind="primary"],[data-testid="stBaseButton-primary"]{background:var(--amarillo) !important;color:#11161C !important;border:0 !important;font-weight:800 !important}
.stButton button[kind="primary"]:hover,[data-testid="stBaseButton-primary"]:hover{background:#FFD23F !important;color:#11161C !important}
[class*="st-key-btn_"] button p{font-size:.8rem;white-space:nowrap}
.stTabs [role="tablist"]{gap:6px;background:var(--tarjeta);border:1px solid var(--borde);border-radius:14px;padding:5px;width:fit-content;max-width:100%}
.stTabs [data-testid="stTab"]{border-radius:10px;padding:8px 16px;color:var(--tenue);height:auto;transition:background .2s ease-out,color .2s ease-out}
.stTabs [data-testid="stTab"] p{font-family:'Sora',sans-serif;font-weight:700;font-size:.92rem}
.stTabs [data-testid="stTab"][aria-selected="true"]{background:rgba(245,184,0,.14);color:var(--amarillo)}
[data-testid="stExpander"] details{background:var(--tarjeta);border:1px solid var(--borde);border-radius:14px}
[data-testid="stExpander"] summary{font-weight:600}
[data-testid="stExpander"] summary:hover{color:var(--amarillo)}
[data-testid="stFileUploaderDropzone"]{background:var(--hundido);border:1px dashed var(--borde2);border-radius:14px}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border:1px solid var(--borde);border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px}
[data-testid="stDeckGlJsonChart"]{border-radius:14px;overflow:hidden}

/* ---------- Pie ---------- */
.rr-pie{margin-top:1.4rem;border-radius:16px;background:var(--tarjeta);border:1px solid var(--borde);color:var(--tenue);padding:16px 22px;
 display:flex;flex-wrap:wrap;gap:8px 28px;justify-content:space-between;font-size:.82rem;border-bottom:3px solid var(--amarillo)}
.rr-pie b{color:var(--texto)}

@media (max-width:640px){
 .rr-hero-txt{padding:18px 18px 124px}.rr-camion{left:26%;width:150px}.rr-luna{display:none}
 .rr-kpis{grid-template-columns:1fr}.rr-sem{flex-direction:column;align-items:flex-start}.rr-luces{flex-direction:row}
 .rr-of{grid-template-columns:30px 1fr}.rr-of .pa{grid-column:2}
}
@media (prefers-reduced-motion:reduce){
 .rr-hero *,.rr-sem,.rr-luces i.on,.rr-picto svg,.rr-fact div,.rr-of{animation:none !important}
 .rr-ben,.stButton button,.stDownloadButton button{transition:none}
}
</style>
"""

LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Logo de RutaRentable">'
    '<rect width="64" height="64" rx="15" fill="#F5B800"/>'
    '<path d="M9 50 C 22 50, 22 38, 34 38 S 46 26, 56 26" fill="none" stroke="#11161C" stroke-width="3" '
    'stroke-linecap="round" stroke-dasharray="1 7"/>'
    '<circle cx="9" cy="50" r="3.6" fill="#11161C"/>'
    '<circle cx="56" cy="26" r="3.6" fill="#22C55E" stroke="#11161C" stroke-width="1.6"/>'
    '<rect x="11" y="13" width="25" height="16" rx="2.5" fill="#11161C"/>'
    '<path d="M38 18 h8 l6 6.5 V29 H38 Z" fill="#11161C"/><path d="M41 20.5 h4.2 l3.2 3.6 H41 Z" fill="#F5B800"/>'
    '<circle cx="19" cy="31" r="4.2" fill="#11161C" stroke="#F5B800" stroke-width="1.8"/>'
    '<circle cx="45" cy="31" r="4.2" fill="#11161C" stroke="#F5B800" stroke-width="1.8"/></svg>'
)


def _rueda(cx):
    return (f'<g class="rr-rueda"><circle cx="{cx}" cy="64" r="11" fill="#0B0F14" stroke="#93A1B0" stroke-width="3"/>'
            f'<path d="M{cx - 7} 64 h14 M{cx} 57 v14" stroke="#5B6876" stroke-width="2.2" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="64" r="2.6" fill="#F5B800"/></g>')


CAMION = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80" aria-hidden="true">'
    '<defs><linearGradient id="rr-haz-g" x1="0" x2="1" y1="0" y2="0">'
    '<stop offset="0" stop-color="#FFE98A" stop-opacity=".75"/><stop offset="1" stop-color="#FFE98A" stop-opacity="0"/>'
    '</linearGradient></defs>'
    '<polygon class="rr-haz" points="178,49 380,22 380,76 178,55" fill="url(#rr-haz-g)"/>'
    '<rect x="6" y="8" width="114" height="48" rx="5" fill="#F5B800"/>'
    '<path d="M18 20 h90 M18 32 h90 M18 44 h90" stroke="rgba(17,22,28,.22)" stroke-width="2.4"/>'
    '<path d="M124 20 h28 l24 21 v15 H124 Z" fill="#E8EDF2"/>'
    '<path d="M132 26 h17 l15 14 H132 Z" fill="#3B82B8"/>'
    '<rect x="6" y="56" width="172" height="6" rx="2" fill="#0B0F14"/>'
    '<rect x="173" y="47" width="6" height="7" rx="1.5" fill="#FFF3B0"/>'
    '<rect x="3" y="46" width="4" height="8" rx="1" fill="#EF4444"/>'
    + _rueda(38) + _rueda(150) + "</svg>"
)

MINI = ('<svg class="{c}" style="animation-delay:{d}ms" viewBox="0 0 32 20" fill="currentColor" aria-hidden="true">'
        '<rect x="1" y="2" width="18" height="12" rx="1.8"/><path d="M20.5 5.5 h5.5 l5 5 v3.5 H20.5 Z"/>'
        '<circle cx="7" cy="16" r="3" stroke="#141B22" stroke-width="1.4"/>'
        '<circle cx="25" cy="16" r="3" stroke="#141B22" stroke-width="1.4"/></svg>')


def _montes(puntos, relleno):
    """Silueta de 1.200 de ancho repetida dos veces para que el desplazamiento sea continuo."""
    d = "M0 120 " + " ".join(f"L{x + dx} {y}" for dx in (0, 1200) for x, y in puntos) + " L2400 120 Z"
    return ('<svg viewBox="0 0 2400 120" preserveAspectRatio="none" aria-hidden="true">'
            f'<path d="{d}" fill="{relleno}"/></svg>')


_LEJOS = [(0, 70), (90, 38), (180, 66), (270, 18), (360, 60), (450, 40), (540, 74), (640, 26), (740, 66),
          (820, 44), (910, 70), (1000, 14), (1090, 58), (1160, 42), (1200, 70)]
_CERCA = [(0, 80), (120, 52), (230, 86), (340, 44), (470, 90), (590, 58), (700, 92), (830, 48), (960, 88),
          (1080, 62), (1200, 80)]
_ESTRELLAS = [(4, 12, 1.2), (11, 30, .9), (19, 8, 1.1), (27, 22, .8), (34, 40, 1), (43, 10, 1.3), (52, 26, .9),
              (61, 14, 1), (68, 34, .8), (76, 7, 1.2), (83, 44, .9), (95, 30, 1)]

ICONO = {
    "ruta": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/>'
            '<path d="M8.5 19 H15 a3.5 3.5 0 0 0 0-7 H9 a3.5 3.5 0 0 1 0-7 h6.5"/></svg>',
    "medidor": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
               'stroke-linejoin="round"><path d="M4 17 a8 8 0 1 1 16 0"/><path d="M12 17 l4-6"/>'
               '<circle cx="12" cy="17" r="1.4" fill="currentColor"/></svg>',
    "peso": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M7 9 h10 l2.5 11 h-15 Z"/><circle cx="12" cy="6" r="2.5"/></svg>',
    "mapa": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M12 21 s6-5.6 6-10.5 a6 6 0 0 0-12 0 C6 15.4 12 21 12 21 Z"/>'
            '<circle cx="12" cy="10.5" r="2.2"/></svg>',
    "caja": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M3 8 l9-4.5 9 4.5 v8.5 l-9 4.5 -9-4.5 Z"/><path d="M3 8 l9 4.5 9-4.5 M12 12.5 V21"/></svg>',
    "reloj": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5 V12 l3 2"/></svg>',
    "trato": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round"><path d="M4 5 h16 v11 H10 l-5 4 v-4 H4 Z"/><path d="M8 9.5 h8 M8 12.5 h5"/></svg>',
    "lista": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round"><path d="M9 6 h11 M9 12 h11 M9 18 h11"/><path d="M3.5 6 l1.2 1.2 2-2.4 M3.5 12 l1.2 1.2 2-2.4 M3.5 18 l1.2 1.2 2-2.4"/></svg>',
    "semaforo": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round"><rect x="8" y="2.5" width="8" height="19" rx="3"/><circle cx="12" cy="7" r="1.3" fill="currentColor"/>'
                '<circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="17" r="1.3" fill="currentColor"/></svg>',
    "lupa": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><circle cx="11" cy="11" r="6.5"/><path d="M16 16 l4.5 4.5"/></svg>',
    "edificio": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round"><path d="M4 21 V5 l8-2 v18 M12 9 l8 2 v10 M3 21 h18 M7.5 8.5 h1 M7.5 12.5 h1 M7.5 16.5 h1 M15.5 14 h1 M15.5 17.5 h1"/></svg>',
}


def hero(chips):
    estrellas = "".join(f'<circle cx="{x}%" cy="{y}%" r="{r}" fill="#E8EDF2"{" class=t" if i % 3 == 0 else ""}/>'
                        for i, (x, y, r) in enumerate(_ESTRELLAS))
    chips_html = "".join(f'<span class="rr-chip">{c}</span>' for c in chips)
    return (
        '<div class="rr-hero">'
        f'<svg class="rr-estrellas" aria-hidden="true">{estrellas}</svg><div class="rr-luna"></div>'
        f'<div class="rr-montes lejos">{_montes(_LEJOS, "#16263B")}</div>'
        f'<div class="rr-montes cerca">{_montes(_CERCA, "#0D1622")}</div>'
        '<div class="rr-hero-txt"><div class="rr-marca">' + LOGO +
        '<div class="rr-nombre">Ruta<span>Rentable</span><small>Riesgo de una oferta de carga en Colombia</small></div></div>'
        '<div class="rr-gancho">¿Te alcanza el flete? <span>Revísalo antes de cargar.</span></div>'
        '<div class="rr-sub">Cuéntanos la ruta y la carga, y te decimos qué tan probable es que ese viaje '
        'no alcance a cubrir tus costos.</div>'
        f'<div class="rr-chips">{chips_html}</div></div>'
        f'<div class="rr-via"><div class="rr-carril"></div></div><div class="rr-camion">{CAMION}</div>'
        '</div>'
    )


PORQUE = (
    '<div class="rr-porque">'
    '<div class="rr-ben"><div class="n">' + ICONO["reloj"] + '</div><div><b>Decide en segundos</b>'
    '<span>Cuatro datos de la oferta y sale el semáforo.</span></div></div>'
    '<div class="rr-ben"><div class="n">' + ICONO["trato"] + '</div><div><b>Negocia con argumentos</b>'
    '<span>Si sale en rojo, tienes con qué pedir más flete.</span></div></div>'
    '<div class="rr-ben"><div class="n">' + ICONO["lista"] + '</div><div><b>Compara tus ofertas</b>'
    '<span>Mete varias y mira cuál te conviene más.</span></div></div>'
    '</div>'
)


def titulo(icono, texto):
    return f'<div class="rr-titulo">{ICONO[icono]}{texto}</div>'


def pista(texto, clase=""):
    return f'<div class="rr-pista {clase}"><i></i><span>{texto}</span></div>'


TITULO_NIVEL = {
    "verde": "Buena oferta: riesgo bajo",
    "ambar": "Revisa con cuidado: está cerca del límite",
    "rojo": "Riesgo alto: pide más flete o revisa la oferta",
}
CORTO_NIVEL = {"verde": "Riesgo bajo", "ambar": "Cerca del límite", "rojo": "Riesgo alto"}


def semaforo(nivel, frase, n_malos):
    luces = "".join(f'<i class="{"on" if nivel == n else ""}"></i>' for n in ("rojo", "ambar", "verde"))
    camiones = "".join(MINI.format(c="m" if i < n_malos else "b", d=40 * i) for i in range(10))
    return (
        f'<div class="rr-sem {nivel}" role="status"><div class="rr-luces" aria-hidden="true">{luces}</div><div>'
        f'<div class="t1">{TITULO_NIVEL[nivel]}</div><div class="t2">{frase}</div>'
        f'<div class="rr-picto" aria-hidden="true">{camiones}</div>'
        '<div class="rr-picto-ley"><i style="background:#EF4444"></i>no alcanzó a cubrir el costo &nbsp; '
        '<i style="background:#22C55E"></i>sí lo cubrió</div>'
        '</div></div>'
    )


def factores(items):
    """items: lista de (tono, texto) con tono en sube / baja / medio."""
    marca = {"sube": "Sube el riesgo", "baja": "Baja el riesgo", "medio": "Ojo"}
    filas = "".join(f'<div class="{t}" style="animation-delay:{80 * i}ms"><em>{marca[t]}</em><span>{x}</span></div>'
                    for i, (t, x) in enumerate(items))
    return f'<div class="rr-fact">{filas}</div>'


def kpis(items):
    """items: lista de (icono, etiqueta, valor, nota)."""
    celdas = "".join(
        f'<div class="rr-kpi"><div class="k">{ICONO[i]}{k}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
        for i, k, v, s in items)
    return f'<div class="rr-kpis">{celdas}</div>'


def leyenda(limite_txt):
    return ('<div class="rr-leyenda">'
            '<span><i style="background:rgba(34,197,94,.55)"></i>Riesgo bajo</span>'
            '<span><i style="background:rgba(245,158,11,.6)"></i>Cerca del límite</span>'
            '<span><i style="background:rgba(239,68,68,.6)"></i>Riesgo alto</span>'
            f'<span><i style="background:#F5B800;width:4px"></i>Límite {limite_txt}</span></div>')


def pastilla(nivel):
    return f'<span class="rr-pastilla" style="--c:{COLOR[nivel]}"><i></i>{CORTO_NIVEL[nivel]}</span>'


def ranking(filas):
    """filas: lista de dicts con nivel, ruta, detalle, frase; ya ordenadas de mejor a peor."""
    partes = []
    for i, f in enumerate(filas):
        sello = '<span class="rr-sello">Mejor opción</span>' if i == 0 else ""
        partes.append(
            f'<div class="rr-of {f["nivel"]}{" mejor" if i == 0 else ""}" style="animation-delay:{70 * i}ms">'
            f'<div class="pos">{i + 1}</div><div><div class="r">{f["ruta"]}{sello}</div>'
            f'<div class="d">{f["detalle"]}</div><div class="f">{f["frase"]}</div></div>'
            f'<div class="pa">{pastilla(f["nivel"])}</div></div>')
    return '<div class="rr-rank">' + "".join(partes) + "</div>"


def caja_umbral(valor):
    return f'<div class="rr-umbral"><span class="k">Límite en uso</span><span class="v">{valor}</span></div>'


PIE = (
    '<div class="rr-pie">'
    '<span><b>Autores:</b> Daniel Pacheco y Harold Burgos</span>'
    '<span><b>Curso:</b> Machine Learning I · Universidad Externado de Colombia · Proyecto Integrador</span>'
    '<span><b>Fuentes:</b> RNDC y SICE-TAC (Ministerio de Transporte, diciembre de 2025) y DIVIPOLA (DANE)</span>'
    '</div>'
)

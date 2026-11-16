import base64
import html
import io
from datetime import date

import pandas as pd
import streamlit as st
from PIL import Image
from sqlalchemy import text

LOGO = Image.open(io.BytesIO(base64.b64decode("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")))
st.set_page_config(page_title="Multas del equipo", page_icon=LOGO, layout="centered")
st.markdown("""<style>
h1, h2, h3 { color: #C8102E !important; }
.stTabs [data-baseweb="tab"] { font-weight: 700; }
.stButton button[kind="primary"], button[kind="primaryFormSubmit"] { background: #C8102E; border-color: #C8102E; color: #fff; }
.qt{width:100%;border-collapse:collapse;border:2px solid #C8102E}
.qt th{background:#9E0B22;color:#fff;padding:8px 10px;text-align:center}
.qt td{padding:8px 10px;text-align:center}.qt td:first-child{text-align:left}
.qt tr.w td{background:#fff;color:#1A1A1A}.qt tr.r td{background:#C8102E;color:#fff}
</style>""", unsafe_allow_html=True)

conn = st.connection("db", type="sql")
ROLE_MULT = {"jugador": 1, "capitán": 2, "entrenador": 2}  # entrenadores y capitanes pagan x2
TAG = {"capitán": " (C)", "entrenador": " (E)"}


def run(q, **p):
    with conn.session as s:
        s.execute(text(q), p)
        s.commit()


q = lambda sql, **p: conn.query(sql, params=p, ttl=0)
eur = lambda x: f"{float(x):.2f} €".replace(".", ",")
dmy = lambda d: pd.to_datetime(d).strftime("%d/%m/%Y")


@st.cache_resource
def init():
    run("CREATE TABLE IF NOT EXISTS fm_players (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)")
    run("ALTER TABLE fm_players ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'jugador'")
    run("CREATE TABLE IF NOT EXISTS fm_catalog (id SERIAL PRIMARY KEY, concept TEXT UNIQUE NOT NULL, amount NUMERIC(8,2) NOT NULL)")
    run("CREATE TABLE IF NOT EXISTS fm_fines (id SERIAL PRIMARY KEY, player_id INT NOT NULL, concept TEXT NOT NULL, "
        "amount NUMERIC(8,2) NOT NULL, fine_date DATE NOT NULL, paid BOOLEAN NOT NULL DEFAULT FALSE, paid_date DATE, note TEXT)")


init()


def table(df):
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join(
        f"<tr class='{'r' if k % 2 else 'w'}'>"
        + "".join(f"<td>{'<b>' if j == 0 else ''}{html.escape(str(v))}{'</b>' if j == 0 else ''}</td>" for j, v in enumerate(row))
        + "</tr>" for k, row in enumerate(df.itertuples(index=False)))
    st.markdown(f"<div style='overflow-x:auto'><table class='qt'><tr>{head}</tr>{body}</table></div>", unsafe_allow_html=True)


def fines():
    """Multas con vencimiento: hay que pagar como máximo el viernes de la semana (si cae en fin de semana, el viernes siguiente).
    Si se paga después (o sigue sin pagar), el importe se duplica."""
    d = q("SELECT f.id, f.player_id, p.name, p.role, f.concept, f.amount, f.fine_date, f.paid, f.paid_date, f.note "
          "FROM fm_fines f JOIN fm_players p ON p.id=f.player_id")
    if d.empty:
        return d
    d["fine_date"] = pd.to_datetime(d.fine_date)
    d["paid"] = d.paid.astype(bool)
    d["amount"] = d.amount.astype(float)
    d["due"] = d.fine_date + pd.to_timedelta((4 - d.fine_date.dt.weekday) % 7, unit="D")
    ref = pd.Series(pd.Timestamp(date.today()), index=d.index).where(~d.paid, pd.to_datetime(d.paid_date).fillna(d.fine_date))
    d["late"] = ref > d.due
    d["eff"] = d.amount * (1 + d.late.astype(int))
    d["over"] = d.late & ~d.paid
    d["pag_e"] = d.eff.where(d.paid, 0.0)
    d["pen_e"] = d.eff.where(~d.paid, 0.0)
    return d


c1, c2 = st.columns([1, 4], vertical_alignment="center")
c1.image(LOGO, width=80)
c2.title("Multas del equipo")

# Código del equipo (opcional): si pones team_code en los Secrets, hay que introducirlo para ver los datos
code = st.secrets.get("team_code")
if code and not st.session_state.get("ok"):
    c = st.text_input("Código del equipo", type="password")
    if c and c == code:
        st.session_state["ok"] = True
        st.rerun()
    elif c:
        st.error("Código incorrecto.")
    st.stop()

pl = q("SELECT id, name, role FROM fm_players ORDER BY name")
d = fines()
t1, t2, t3 = st.tabs(["Resumen", "Multas", "Organizador"])

# ---------- Resumen ----------
with t1:
    if pl.empty:
        st.write("Todavía no hay jugadores cargados.")
    else:
        g = pd.DataFrame({"id": pl.id, "Jugador": pl.name + pl.role.map(lambda r: TAG.get(r, ""))})
        if d.empty:
            g[["n", "tot", "pag", "pen", "dup"]] = 0
        else:
            ag = d.groupby("player_id").agg(n=("id", "count"), tot=("eff", "sum"), pag=("pag_e", "sum"), pen=("pen_e", "sum"), dup=("over", "sum"))
            g = g.merge(ag, left_on="id", right_index=True, how="left").fillna(0)
        g = g.sort_values(["pen", "Jugador"], ascending=[False, True])
        a, b, c = st.columns(3)
        a.metric("Total", eur(g.tot.sum()))
        b.metric("Pagado", eur(g.pag.sum()))
        c.metric("Pendiente", eur(g.pen.sum()))
        risk = list(g.loc[g.dup > 0, "Jugador"])
        if risk:
            st.warning("Multas duplicadas sin pagar (posible desconvocatoria): " + ", ".join(risk))
        table(pd.DataFrame({"Jugador": g["Jugador"], "Multas": g.n.astype(int), "Total": g.tot.map(eur),
                            "Pagado": g.pag.map(eur), "Debe": g.pen.map(eur)}))
        st.caption("(C) capitán · (E) entrenador. Las multas se pagan como máximo el viernes de la semana; si no, se duplican.")

# ---------- Multas ----------
with t2:
    who = st.selectbox("Jugador", ["Todos"] + list(pl.name))
    v = d if d.empty or who == "Todos" else d[d.name == who]
    if v.empty:
        st.write("Sin multas.")
    else:
        v = v.sort_values(["fine_date", "id"], ascending=False)
        if who != "Todos":
            st.metric("Debe", eur(v.pen_e.sum()))
        est = [f"Pagada {dmy(pdt)}" if p and pd.notna(pdt) else "Pagada" if p else
               (f"DUPLICADA (venció {dmy(du)})" if o else f"Pendiente (vence {dmy(du)})")
               for p, pdt, o, du in zip(v.paid, v.paid_date, v.over, v.due)]
        out = pd.DataFrame({"Fecha": v.fine_date.map(dmy), "Jugador": v["name"],
                            "Multa": v.concept + v.note.fillna("").map(lambda x: f" ({x})" if x else ""),
                            "Importe": v.eff.map(eur), "Estado": est})
        table(out.drop(columns="Jugador") if who != "Todos" else out)

# ---------- Organizador ----------
with t3:
    pw = st.text_input("Contraseña de organizador", type="password")
    if not pw:
        st.stop()
    if pw != st.secrets.get("admin_password"):
        st.error("Contraseña incorrecta.")
        st.stop()
    cat = q("SELECT concept, amount FROM fm_catalog ORDER BY id")
    roles = dict(zip(pl.name, pl.role))

    st.subheader("Poner una multa")
    if pl.empty or cat.empty:
        st.info("Primero carga los jugadores y las multas más abajo.")
    else:
        sel = st.multiselect("Jugadores", list(pl.name))
        con = st.selectbox("Multa", list(cat.concept))
        base = st.number_input("Importe base (€)", 0.0, 500.0, float(cat.set_index("concept").loc[con, "amount"]), 0.5, key=f"am{con}")
        qty = st.number_input("Cantidad (por ejemplo, prendas que faltan)", 1, 20, 1)
        fd = st.date_input("Fecha", date.today())
        nt = st.text_input("Nota (opcional)", max_chars=60)
        for n in sel:
            st.caption(f"{n}: {eur(base * qty * ROLE_MULT[roles[n]])}" + (f" (x{ROLE_MULT[roles[n]]} por {roles[n]})" if ROLE_MULT[roles[n]] > 1 else ""))
        if st.button("Poner multa", type="primary"):
            if not sel:
                st.error("Elige al menos un jugador.")
            else:
                ids = dict(zip(pl.name, pl.id))
                for n in sel:
                    parts = ([f"x{qty}"] if qty > 1 else []) + ([f"{roles[n]} x2"] if ROLE_MULT[roles[n]] > 1 else []) + ([nt] if nt else [])
                    run("INSERT INTO fm_fines (player_id, concept, amount, fine_date, note) VALUES (:p,:c,:a,:d,:n)",
                        p=int(ids[n]), c=con, a=base * qty * ROLE_MULT[roles[n]], d=fd, n=", ".join(parts) or None)
                st.success(f"Multa puesta a {len(sel)} jugador(es). Recarga la página.")

    st.subheader("Pagos")
    if not pl.empty:
        pj = st.selectbox("Jugador", list(pl.name), key="pj")
        mine = d[d.name == pj].sort_values("fine_date") if not d.empty else d
        lab = {int(r.id): f"{dmy(r.fine_date)} · {r.concept} · {eur(r.eff)}" for r in mine[~mine.paid].itertuples()} if not mine.empty else {}
        ch = st.multiselect("Multas pendientes que ha pagado", list(lab), format_func=lab.get)
        if st.button("Marcar como pagadas") and ch:
            for i in ch:
                run("UPDATE fm_fines SET paid=TRUE, paid_date=:d WHERE id=:i", d=date.today(), i=i)
            st.success("Hecho. Recarga la página.")
        lab2 = {int(r.id): f"{dmy(r.fine_date)} · {r.concept} · {eur(r.eff)}" for r in mine.itertuples()} if not mine.empty else {}
        bo = st.selectbox("Borrar una multa (por error)", [None] + list(lab2), format_func=lambda x: "—" if x is None else lab2[x])
        if bo is not None and st.button("Borrar multa seleccionada"):
            run("DELETE FROM fm_fines WHERE id=:i", i=bo)
            st.success("Multa borrada. Recarga la página.")

    st.subheader("Jugadores")
    st.caption("Uno por línea. Para capitanes o entrenadores: Nombre;capitán  o  Nombre;entrenador (pagan x2)")
    new = st.text_area("Añadir jugadores")
    if st.button("Añadir jugadores"):
        for ln in [x.strip() for x in new.splitlines() if x.strip()]:
            n, _, r = ln.partition(";")
            r = r.strip().lower().replace("capitan", "capitán")
            run("INSERT INTO fm_players (name, role) VALUES (:n,:r) ON CONFLICT (name) DO UPDATE SET role=EXCLUDED.role",
                n=n.strip(), r=r if r in ROLE_MULT else "jugador")
        st.success("Jugadores añadidos. Recarga la página.")
    if not pl.empty:
        rj = st.selectbox("Cambiar el rol de", list(pl.name), key="rj")
        rr = st.selectbox("Rol", list(ROLE_MULT), index=list(ROLE_MULT).index(roles[rj]), key=f"rr{rj}")
        if st.button("Guardar rol"):
            run("UPDATE fm_players SET role=:r WHERE name=:n", r=rr, n=rj)
            st.success("Rol cambiado. Afecta solo a las multas nuevas. Recarga la página.")
        rm = st.selectbox("Quitar un jugador (y sus multas)", [None] + list(pl.name), format_func=lambda x: "—" if x is None else x)
        if rm and st.checkbox(f"Confirmo que quiero borrar a {rm} y todas sus multas") and st.button("Quitar jugador"):
            pid = int(pl.set_index("name").loc[rm, "id"])
            run("DELETE FROM fm_fines WHERE player_id=:i", i=pid)
            run("DELETE FROM fm_players WHERE id=:i", i=pid)
            st.success("Jugador quitado. Recarga la página.")

    st.subheader("Listado de multas")
    st.caption("Una por línea con el formato  Concepto;importe  (por ejemplo: Llegar tarde;1)")
    lst = st.text_area("Cargar o actualizar multas")
    if st.button("Cargar multas"):
        n_ok = 0
        for ln in lst.splitlines():
            if ";" in ln:
                cn, am_ = ln.rsplit(";", 1)
                try:
                    run("INSERT INTO fm_catalog (concept, amount) VALUES (:c,:a) ON CONFLICT (concept) DO UPDATE SET amount=EXCLUDED.amount",
                        c=cn.strip(), a=float(am_.replace(",", ".").replace("€", "").strip()))
                    n_ok += 1
                except ValueError:
                    st.warning(f"No entiendo el importe de: {ln}")
        st.success(f"{n_ok} multas cargadas. Recarga la página.")
    if not cat.empty:
        table(pd.DataFrame({"Multa": cat.concept, "Importe": cat.amount.map(eur)}))

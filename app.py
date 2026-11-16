import html
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import text

st.set_page_config(page_title="Multas del equipo", page_icon="🟥", layout="centered")
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


st.title("🟥 Multas del equipo")

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

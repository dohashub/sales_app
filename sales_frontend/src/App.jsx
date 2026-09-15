import React, { useState, useEffect, useCallback } from "react";

/* ---------------------------------------------------------------------
   Design tokens — white body, baby-blue accent throughout: tables,
   focus rings, and the search box all pick up the same soft blue.
--------------------------------------------------------------------- */
const FONT_MONO = "'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace";
const FONT_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

const C = {
  bg: "#FFFFFF",
  surface: "#FAFAFA",
  card: "#FFFFFF",
  ink: "#18181B",
  inkFaint: "#71717A",
  line: "#D9EAF3",
  accent: "#2FA0D6",
  accentText: "#1E7FAE",
  accentSoft: "#E9F6FC",
  stripe: "#F5FBFE",
  hoverBg: "#DEF1FA",
  blue: "#2563EB",
  blueSoft: "#EFF4FF",
  danger: "#DC2626",
  dangerSoft: "#FDEEEE",
  ok: "#2FA0D6",
  okSoft: "#E9F6FC",
};

const TABS = [
  { key: "customers", label: "Customers" },
  { key: "products", label: "Products" },
  { key: "priceLists", label: "Price Lists" },
  { key: "priceListItems", label: "Price List Items" },
  { key: "receipts", label: "Receipts" },
];

/* ---------------------------------------------------------------------
   Generic data hook — GET a list, expose reload + mutate helpers
--------------------------------------------------------------------- */
function useList(apiBase, path, active) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(() => {
    if (!active) return;
    setLoading(true);
    setError(null);
    fetch(`${apiBase}${path}`)
      .then(async (res) => {
        const body = await res.json().catch(() => null);
        if (!res.ok) throw new Error((body && body.message) || `Couldn't load ${path} (${res.status})`);
        setData(Array.isArray(body) ? body : []);
      })
      .catch((err) => {
        // Surface network-level failures ("Failed to fetch") distinctly from
        // API error responses, since the fix for each is different.
        if (err instanceof TypeError) {
          setError(`Couldn't reach the server at ${apiBase}. Check that the API is running and reachable.`);
        } else {
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  }, [apiBase, path, active]);

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiBase, path, active]);

  return { data, loading, error, reload, setError };
}

async function send(apiBase, path, method, body) {
  let res;
  try {
    res = await fetch(`${apiBase}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(`Couldn't reach the server at ${apiBase}. Check that the API is running and reachable.`);
  }
  let parsed = null;
  try {
    parsed = await res.json();
  } catch (e) {
    /* no body */
  }
  if (!res.ok) {
    throw new Error((parsed && parsed.message) || `Request failed (${res.status})`);
  }
  return parsed;
}

/* ---------------------------------------------------------------------
   Small UI atoms
--------------------------------------------------------------------- */
function Banner({ tone = "error", children, onDismiss }) {
  if (!children) return null;
  const bg = tone === "error" ? C.dangerSoft : C.okSoft;
  const fg = tone === "error" ? C.danger : C.ok;
  return (
    <div
      style={{
        background: bg,
        color: fg,
        border: `1px solid ${fg}33`,
        borderRadius: 4,
        padding: "9px 12px",
        fontSize: 13,
        fontFamily: FONT_SANS,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 12,
        marginBottom: 14,
      }}
    >
      <span>{children}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            background: "none",
            border: "none",
            color: fg,
            cursor: "pointer",
            fontSize: 15,
            lineHeight: 1,
            padding: 0,
          }}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4, fontFamily: FONT_SANS }}>
      <span style={{ fontSize: 11.5, color: C.inkFaint, letterSpacing: 0.2 }}>{label}</span>
      {children}
    </label>
  );
}

const inputStyle = {
  fontFamily: FONT_SANS,
  fontSize: 13.5,
  padding: "7px 9px",
  borderRadius: 4,
  border: `1px solid ${C.line}`,
  background: "#fff",
  color: C.ink,
  outline: "none",
};

function TextInput({ className, ...props }) {
  return <input {...props} className={`app-input ${className || ""}`} style={{ ...inputStyle, ...(props.style || {}) }} />;
}

function Select({ children, className, ...props }) {
  return (
    <select {...props} className={`app-input ${className || ""}`} style={{ ...inputStyle, ...(props.style || {}) }}>
      {children}
    </select>
  );
}

function Btn({ variant = "primary", style, ...props }) {
  const base = {
    fontFamily: FONT_SANS,
    fontSize: 13,
    fontWeight: 600,
    padding: "7px 14px",
    borderRadius: 4,
    cursor: "pointer",
    border: "1px solid transparent",
    transition: "opacity 120ms ease",
  };
  const variants = {
    primary: { background: C.blue, color: "#fff" },
    ghost: { background: "transparent", color: C.ink, border: `1px solid ${C.line}` },
    danger: { background: "transparent", color: C.danger, border: `1px solid ${C.danger}55` },
  };
  return <button {...props} style={{ ...base, ...variants[variant], ...style }} />;
}

/* Simple client-side search box: filters the already-loaded list
   instantly, no extra requests to a backend that may be flaky.
   Styled as a filled blue pill with a search icon so it reads as
   its own thing rather than blending into the form fields above. */
function SearchInput({ value, onChange, placeholder }) {
  return (
    <div style={{ position: "relative", width: 260, maxWidth: "100%" }}>
      <span
        style={{
          position: "absolute",
          left: 11,
          top: "50%",
          transform: "translateY(-50%)",
          color: C.accentText,
          display: "flex",
          pointerEvents: "none",
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </span>
      <input
        className="app-input app-search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          ...inputStyle,
          width: "100%",
          borderRadius: 999,
          border: `1.5px solid ${C.accentSoft}`,
          background: C.accentSoft,
          color: C.ink,
          padding: value ? "8px 30px 8px 32px" : "8px 12px 8px 32px",
          fontSize: 13.5,
        }}
      />
      {value && (
        <button
          onClick={() => onChange("")}
          aria-label="Clear search"
          style={{
            position: "absolute",
            right: 9,
            top: "50%",
            transform: "translateY(-50%)",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: C.accentText,
            fontSize: 15,
            lineHeight: 1,
            padding: 2,
          }}
        >
          ×
        </button>
      )}
    </div>
  );
}

function Toolbar({ search, onSearch, placeholder, shown, total }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, gap: 12, flexWrap: "wrap" }}>
      <SearchInput value={search} onChange={onSearch} placeholder={placeholder} />
      <span style={{ fontSize: 12, color: C.inkFaint, fontFamily: FONT_SANS }}>
        {shown} of {total}
      </span>
    </div>
  );
}

/* Columns can be plain strings (left-aligned) or { label, align }.
   Header alignment always matches its column's cell alignment so
   figures line up under their headings instead of drifting left. */
function normalizeColumn(c) {
  return typeof c === "string" ? { label: c, align: "left" } : c;
}

function Table({ columns, children, empty }) {
  const cols = columns.map(normalizeColumn);
  return (
    <div style={{ overflowX: "auto", border: `1px solid ${C.line}`, borderRadius: 6 }}>
      <table className="app-table" style={{ width: "100%", borderCollapse: "collapse", fontFamily: FONT_SANS, tableLayout: "fixed" }}>
        <thead>
          <tr>
            {cols.map((c) => (
              <th
                key={c.label}
                style={{
                  textAlign: c.align,
                  fontSize: 11,
                  color: C.accentText,
                  fontWeight: 700,
                  letterSpacing: 0.3,
                  padding: "9px 12px",
                  borderBottom: `1px solid ${C.line}`,
                  background: C.accentSoft,
                }}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
      {empty && (
        <div style={{ padding: "22px 14px", textAlign: "center", color: C.inkFaint, fontSize: 13, fontFamily: FONT_SANS }}>
          {empty}
        </div>
      )}
    </div>
  );
}

function Td({ children, mono, align = "left", width, colSpan }) {
  return (
    <td
      colSpan={colSpan}
      style={{
        padding: "9px 12px",
        borderBottom: `1px solid ${C.line}`,
        fontSize: 13.5,
        color: C.ink,
        fontFamily: mono ? FONT_MONO : FONT_SANS,
        width,
        textAlign: align,
        verticalAlign: "middle",
      }}
    >
      {children}
    </td>
  );
}

function Panel({ title, subtitle, children }) {
  return (
    <div>
      <div style={{ marginBottom: 18 }}>
        <h2 style={{ fontFamily: FONT_SANS, fontWeight: 600, fontSize: 19, margin: 0, color: C.ink }}>{title}</h2>
        {subtitle && <p style={{ margin: "4px 0 0", color: C.inkFaint, fontSize: 13, fontFamily: FONT_SANS }}>{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function SectionCard({ children }) {
  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.line}`,
        borderRadius: 6,
        padding: 16,
        marginBottom: 20,
      }}
    >
      {children}
    </div>
  );
}

function money(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString();
}

function matches(search, ...fields) {
  const q = search.trim().toLowerCase();
  if (!q) return true;
  return fields.some((f) => String(f ?? "").toLowerCase().includes(q));
}

/* ---------------------------------------------------------------------
   Customers
--------------------------------------------------------------------- */
function CustomersPanel({ apiBase, active }) {
  const { data: customers, loading, error, reload, setError } = useList(apiBase, "/customers", active);
  const { data: priceLists } = useList(apiBase, "/price-list", active);

  const [form, setForm] = useState({ name: "", price_list_id: "" });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", price_list_id: "" });
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [search, setSearch] = useState("");

  const priceListLabel = (id) => {
    const pl = priceLists.find((p) => p.price_list_id === id);
    return pl ? pl.price_list_type : `#${id}`;
  };

  const filtered = customers.filter((c) => matches(search, c.customer_id, c.name, priceListLabel(c.price_list_id)));

  async function handleAdd(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, "/customers", "POST", {
        name: form.name,
        price_list_id: Number(form.price_list_id),
      });
      setForm({ name: "", price_list_id: "" });
      setNotice("Customer added.");
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function startEdit(c) {
    setEditingId(c.customer_id);
    setEditForm({ name: c.name, price_list_id: String(c.price_list_id) });
  }

  async function saveEdit(id) {
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, `/customers/${id}`, "PUT", {
        name: editForm.name,
        price_list_id: Number(editForm.price_list_id),
      });
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Remove this customer?")) return;
    setError(null);
    try {
      await send(apiBase, `/customers/${id}`, "DELETE");
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Customers" subtitle="Who you sell to, and the price list each one shops from.">
      <Banner tone="error" onDismiss={() => setError(null)}>{error}</Banner>
      <Banner tone="ok" onDismiss={() => setNotice(null)}>{notice}</Banner>

      <SectionCard>
        <form onSubmit={handleAdd} style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <Field label="Name">
            <TextInput
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Ahmed"
            />
          </Field>
          <Field label="Price list">
            <Select
              required
              value={form.price_list_id}
              onChange={(e) => setForm({ ...form, price_list_id: e.target.value })}
            >
              <option value="" disabled>Choose one</option>
              {priceLists.map((p) => (
                <option key={p.price_list_id} value={p.price_list_id}>{p.price_list_type}</option>
              ))}
            </Select>
          </Field>
          <Btn type="submit" disabled={busy}>Add customer</Btn>
        </form>
      </SectionCard>

      <Toolbar search={search} onSearch={setSearch} placeholder="Search customers..." shown={filtered.length} total={customers.length} />

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Name", align: "left" },
          { label: "Price list", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={!loading && customers.length === 0 ? "No customers yet — add one above." : (!loading && filtered.length === 0 ? "No customers match your search." : null)}
      >
        {filtered.map((c) => {
          const isEditing = editingId === c.customer_id;
          return (
            <tr key={c.customer_id}>
              <Td mono align="right">{c.customer_id}</Td>
              <Td>
                {isEditing ? (
                  <TextInput value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
                ) : (
                  c.name
                )}
              </Td>
              <Td>
                {isEditing ? (
                  <Select value={editForm.price_list_id} onChange={(e) => setEditForm({ ...editForm, price_list_id: e.target.value })}>
                    {priceLists.map((p) => (
                      <option key={p.price_list_id} value={p.price_list_id}>{p.price_list_type}</option>
                    ))}
                  </Select>
                ) : (
                  priceListLabel(c.price_list_id)
                )}
              </Td>
              <Td align="right" width={160}>
                {isEditing ? (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn variant="primary" onClick={() => saveEdit(c.customer_id)} disabled={busy}>Save</Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>Cancel</Btn>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn variant="ghost" onClick={() => startEdit(c)}>Edit</Btn>
                    <Btn variant="danger" onClick={() => handleDelete(c.customer_id)}>Delete</Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Products
--------------------------------------------------------------------- */
function ProductsPanel({ apiBase, active }) {
  const { data: products, loading, error, reload, setError } = useList(apiBase, "/products", active);
  const [form, setForm] = useState({ name: "", stock: "" });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", stock: "", is_active: 1 });
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = products.filter((p) => matches(search, p.product_id, p.name));

  async function handleAdd(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, "/products", "POST", { name: form.name, stock: Number(form.stock) });
      setForm({ name: "", stock: "" });
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function startEdit(p) {
    setEditingId(p.product_id);
    setEditForm({ name: p.name, stock: String(p.stock), is_active: p.is_active });
  }

  async function saveEdit(id) {
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, `/products/${id}`, "PUT", {
        name: editForm.name,
        stock: Number(editForm.stock),
        is_active: Number(editForm.is_active),
      });
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this product? If it's used in past receipts, deactivate it instead.")) return;
    setError(null);
    try {
      await send(apiBase, `/products/${id}`, "DELETE");
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Products" subtitle="Stock on hand and whether an item can still be sold.">
      <Banner tone="error" onDismiss={() => setError(null)}>{error}</Banner>

      <SectionCard>
        <form onSubmit={handleAdd} style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <Field label="Name">
            <TextInput required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Pen" />
          </Field>
          <Field label="Stock">
            <TextInput required type="number" min="0" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} />
          </Field>
          <Btn type="submit" disabled={busy}>Add product</Btn>
        </form>
      </SectionCard>

      <Toolbar search={search} onSearch={setSearch} placeholder="Search products..." shown={filtered.length} total={products.length} />

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Name", align: "left" },
          { label: "Stock", align: "right" },
          { label: "Active", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={!loading && products.length === 0 ? "No products yet — add one above." : (!loading && filtered.length === 0 ? "No products match your search." : null)}
      >
        {filtered.map((p) => {
          const isEditing = editingId === p.product_id;
          return (
            <tr key={p.product_id}>
              <Td mono align="right">{p.product_id}</Td>
              <Td>{isEditing ? <TextInput value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /> : p.name}</Td>
              <Td mono align="right">
                {isEditing ? (
                  <TextInput type="number" min="0" style={{ width: 90 }} value={editForm.stock} onChange={(e) => setEditForm({ ...editForm, stock: e.target.value })} />
                ) : (
                  p.stock
                )}
              </Td>
              <Td>
                {isEditing ? (
                  <Select value={editForm.is_active} onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value })}>
                    <option value={1}>Active</option>
                    <option value={0}>Inactive</option>
                  </Select>
                ) : (
                  <span
                    style={{
                      fontFamily: FONT_SANS,
                      fontSize: 12,
                      padding: "2px 8px",
                      borderRadius: 3,
                      background: p.is_active ? C.accentSoft : C.dangerSoft,
                      color: p.is_active ? C.accent : C.danger,
                    }}
                  >
                    {p.is_active ? "Active" : "Inactive"}
                  </span>
                )}
              </Td>
              <Td align="right" width={160}>
                {isEditing ? (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn onClick={() => saveEdit(p.product_id)} disabled={busy}>Save</Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>Cancel</Btn>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn variant="ghost" onClick={() => startEdit(p)}>Edit</Btn>
                    <Btn variant="danger" onClick={() => handleDelete(p.product_id)}>Delete</Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Price Lists
--------------------------------------------------------------------- */
function PriceListsPanel({ apiBase, active }) {
  const { data: lists, loading, error, reload, setError } = useList(apiBase, "/price-list", active);
  const [form, setForm] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = lists.filter((pl) => matches(search, pl.price_list_id, pl.price_list_type));

  async function handleAdd(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, "/price-list", "POST", { price_list_type: form });
      setForm("");
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function saveEdit(id) {
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, `/price-list/${id}`, "PUT", { price_list_type: editValue });
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this price list?")) return;
    setError(null);
    try {
      await send(apiBase, `/price-list/${id}`, "DELETE");
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Price Lists" subtitle="Named tiers — Retail, Wholesale, and so on — that customers are assigned to.">
      <Banner tone="error" onDismiss={() => setError(null)}>{error}</Banner>

      <SectionCard>
        <form onSubmit={handleAdd} style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <Field label="Price list name">
            <TextInput required value={form} onChange={(e) => setForm(e.target.value)} placeholder="e.g. Wholesale" />
          </Field>
          <Btn type="submit" disabled={busy}>Add price list</Btn>
        </form>
      </SectionCard>

      <Toolbar search={search} onSearch={setSearch} placeholder="Search price lists..." shown={filtered.length} total={lists.length} />

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Type", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={!loading && lists.length === 0 ? "No price lists yet — add one above." : (!loading && filtered.length === 0 ? "No price lists match your search." : null)}
      >
        {filtered.map((pl) => {
          const isEditing = editingId === pl.price_list_id;
          return (
            <tr key={pl.price_list_id}>
              <Td mono align="right">{pl.price_list_id}</Td>
              <Td>
                {isEditing ? (
                  <TextInput value={editValue} onChange={(e) => setEditValue(e.target.value)} />
                ) : (
                  pl.price_list_type
                )}
              </Td>
              <Td align="right" width={160}>
                {isEditing ? (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn onClick={() => saveEdit(pl.price_list_id)} disabled={busy}>Save</Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>Cancel</Btn>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn variant="ghost" onClick={() => { setEditingId(pl.price_list_id); setEditValue(pl.price_list_type); }}>Edit</Btn>
                    <Btn variant="danger" onClick={() => handleDelete(pl.price_list_id)}>Delete</Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Price List Items
--------------------------------------------------------------------- */
function PriceListItemsPanel({ apiBase, active }) {
  const { data: items, loading, error, reload, setError } = useList(apiBase, "/price-list-items", active);
  const { data: priceLists } = useList(apiBase, "/price-list", active);
  const { data: products } = useList(apiBase, "/products", active);

  const [form, setForm] = useState({ price_list_id: "", product_id: "", price: "" });
  const [editingId, setEditingId] = useState(null);
  const [editPrice, setEditPrice] = useState("");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");

  const plLabel = (id) => priceLists.find((p) => p.price_list_id === id)?.price_list_type ?? `#${id}`;
  const prodLabel = (id) => products.find((p) => p.product_id === id)?.name ?? `#${id}`;

  const filtered = items.filter((it) => matches(search, it.id, plLabel(it.price_list_id), prodLabel(it.product_id), it.price));

  async function handleAdd(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, "/price-list-items", "POST", {
        price_list_id: Number(form.price_list_id),
        product_id: Number(form.product_id),
        price: Number(form.price),
      });
      setForm({ price_list_id: "", product_id: "", price: "" });
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function saveEdit(id) {
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, `/price-list-items/${id}`, "PUT", { price: Number(editPrice) });
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Remove this price list item?")) return;
    setError(null);
    try {
      await send(apiBase, `/price-list-items/${id}`, "DELETE");
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Price List Items" subtitle="What each product costs on each price list.">
      <Banner tone="error" onDismiss={() => setError(null)}>{error}</Banner>

      <SectionCard>
        <form onSubmit={handleAdd} style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <Field label="Price list">
            <Select required value={form.price_list_id} onChange={(e) => setForm({ ...form, price_list_id: e.target.value })}>
              <option value="" disabled>Choose one</option>
              {priceLists.map((p) => (
                <option key={p.price_list_id} value={p.price_list_id}>{p.price_list_type}</option>
              ))}
            </Select>
          </Field>
          <Field label="Product">
            <Select required value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
              <option value="" disabled>Choose one</option>
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>{p.name}</option>
              ))}
            </Select>
          </Field>
          <Field label="Price">
            <TextInput required type="number" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
          </Field>
          <Btn type="submit" disabled={busy}>Add item</Btn>
        </form>
      </SectionCard>

      <Toolbar search={search} onSearch={setSearch} placeholder="Search by product or list..." shown={filtered.length} total={items.length} />

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Price list", align: "left" },
          { label: "Product", align: "left" },
          { label: "Price", align: "right" },
          { label: "", align: "right" },
        ]}
        empty={!loading && items.length === 0 ? "No price list items yet — add one above." : (!loading && filtered.length === 0 ? "No items match your search." : null)}
      >
        {filtered.map((it) => {
          const isEditing = editingId === it.id;
          return (
            <tr key={it.id}>
              <Td mono align="right">{it.id}</Td>
              <Td>{plLabel(it.price_list_id)}</Td>
              <Td>{prodLabel(it.product_id)}</Td>
              <Td mono align="right">
                {isEditing ? (
                  <TextInput type="number" min="0" style={{ width: 90 }} value={editPrice} onChange={(e) => setEditPrice(e.target.value)} />
                ) : (
                  money(it.price)
                )}
              </Td>
              <Td align="right" width={160}>
                {isEditing ? (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn onClick={() => saveEdit(it.id)} disabled={busy}>Save</Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>Cancel</Btn>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <Btn variant="ghost" onClick={() => { setEditingId(it.id); setEditPrice(String(it.price)); }}>Edit</Btn>
                    <Btn variant="danger" onClick={() => handleDelete(it.id)}>Delete</Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Receipts
--------------------------------------------------------------------- */
function ReceiptsPanel({ apiBase, active }) {
  const { data: receipts, loading, error, reload, setError } = useList(apiBase, "/receipts", active);
  const { data: customers } = useList(apiBase, "/customers", active);
  const { data: products } = useList(apiBase, "/products", active);

  const [customerId, setCustomerId] = useState("");
  const [lines, setLines] = useState([{ product_id: "", quantity: "1" }]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [openId, setOpenId] = useState(null);
  const [search, setSearch] = useState("");

  const customerLabel = (id) => customers.find((c) => c.customer_id === id)?.name ?? `#${id}`;
  const productLabel = (id) => products.find((p) => p.product_id === id)?.name ?? `#${id}`;

  const filtered = receipts.filter((r) => matches(search, r["receipt#"], customerLabel(r.customer_id), r.date, r.total));

  function updateLine(idx, patch) {
    setLines((ls) => ls.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }
  function addLine() {
    setLines((ls) => [...ls, { product_id: "", quantity: "1" }]);
  }
  function removeLine(idx) {
    setLines((ls) => ls.filter((_, i) => i !== idx));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const items = lines
        .filter((l) => l.product_id)
        .map((l) => ({ product_id: Number(l.product_id), quantity: Number(l.quantity) }));
      if (items.length === 0) throw new Error("Add at least one item to the receipt.");
      await send(apiBase, "/receipts", "POST", { customer_id: Number(customerId), items });
      setCustomerId("");
      setLines([{ product_id: "", quantity: "1" }]);
      setNotice("Receipt created.");
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel title="Receipts" subtitle="Sales, priced from the customer's own price list and deducted from stock.">
      <Banner tone="error" onDismiss={() => setError(null)}>{error}</Banner>
      <Banner tone="ok" onDismiss={() => setNotice(null)}>{notice}</Banner>

      <SectionCard>
        <form onSubmit={handleCreate}>
          <div style={{ display: "flex", gap: 12, marginBottom: 14, flexWrap: "wrap" }}>
            <Field label="Customer">
              <Select required value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
                <option value="" disabled>Choose one</option>
                {customers.map((c) => (
                  <option key={c.customer_id} value={c.customer_id}>{c.name}</option>
                ))}
              </Select>
            </Field>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
            {lines.map((l, idx) => (
              <div key={idx} style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
                <Field label="Product">
                  <Select value={l.product_id} onChange={(e) => updateLine(idx, { product_id: e.target.value })}>
                    <option value="">Choose one</option>
                    {products.map((p) => (
                      <option key={p.product_id} value={p.product_id}>{p.name} ({p.stock} in stock)</option>
                    ))}
                  </Select>
                </Field>
                <Field label="Quantity">
                  <TextInput
                    type="number"
                    min="1"
                    style={{ width: 90 }}
                    value={l.quantity}
                    onChange={(e) => updateLine(idx, { quantity: e.target.value })}
                  />
                </Field>
                {lines.length > 1 && (
                  <Btn type="button" variant="danger" onClick={() => removeLine(idx)}>Remove</Btn>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <Btn type="button" variant="ghost" onClick={addLine}>Add another item</Btn>
            <Btn type="submit" disabled={busy}>Create receipt</Btn>
          </div>
        </form>
      </SectionCard>

      <Toolbar search={search} onSearch={setSearch} placeholder="Search receipts..." shown={filtered.length} total={receipts.length} />

      <Table
        columns={[
          { label: "Receipt #", align: "right" },
          { label: "Customer", align: "left" },
          { label: "Date", align: "left" },
          { label: "Total", align: "right" },
          { label: "", align: "right" },
        ]}
        empty={!loading && receipts.length === 0 ? "No receipts yet — create one above." : (!loading && filtered.length === 0 ? "No receipts match your search." : null)}
      >
        {filtered.map((r) => {
          const rn = r["receipt#"];
          const isOpen = openId === rn;
          return (
            <React.Fragment key={rn}>
              <tr>
                <Td mono align="right">{rn}</Td>
                <Td>{customerLabel(r.customer_id)}</Td>
                <Td mono>{r.date}</Td>
                <Td mono align="right">{money(r.total)}</Td>
                <Td align="right" width={120}>
                  <Btn variant="ghost" onClick={() => setOpenId(isOpen ? null : rn)}>
                    {isOpen ? "Hide items" : "Show items"}
                  </Btn>
                </Td>
              </tr>
              {isOpen && (
                <tr>
                  <Td colSpan={5}>
                    <div style={{ padding: "6px 4px 10px" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: FONT_SANS }}>
                        <thead>
                          <tr>
                            <th style={{ textAlign: "left", padding: "4px 8px", fontSize: 11, color: C.accentText, fontWeight: 700 }}>Item</th>
                            <th style={{ textAlign: "right", padding: "4px 8px", fontSize: 11, color: C.accentText, fontWeight: 700 }}>Quantity</th>
                            <th style={{ textAlign: "right", padding: "4px 8px", fontSize: 11, color: C.accentText, fontWeight: 700 }}>Price</th>
                            <th style={{ textAlign: "right", padding: "4px 8px", fontSize: 11, color: C.accentText, fontWeight: 700 }}>Subtotal</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(r.items || []).map((it, i) => (
                            <tr key={i}>
                              <td style={{ padding: "5px 8px", fontSize: 13, color: C.ink }}>{productLabel(it.product_id)}</td>
                              <td style={{ padding: "5px 8px", fontSize: 13, color: C.ink, textAlign: "right", fontFamily: FONT_MONO }}>{it.quantity}</td>
                              <td style={{ padding: "5px 8px", fontSize: 13, color: C.ink, textAlign: "right", fontFamily: FONT_MONO }}>{money(it.price)}</td>
                              <td style={{ padding: "5px 8px", fontSize: 13, color: C.ink, textAlign: "right", fontFamily: FONT_MONO }}>{money(it.price * it.quantity)}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td colSpan={3} style={{ padding: "7px 8px", textAlign: "right", fontWeight: 700, color: C.ink, borderTop: `1px solid ${C.line}` }}>
                              Total
                            </td>
                            <td style={{ padding: "7px 8px", textAlign: "right", fontWeight: 700, color: C.ink, fontFamily: FONT_MONO, borderTop: `1px solid ${C.line}` }}>
                              {money(r.total)}
                            </td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </Td>
                </tr>
              )}
            </React.Fragment>
          );
        })}
      </Table>
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   App shell
--------------------------------------------------------------------- */
export default function App() {
  const [apiBase, setApiBase] = useState("http://localhost:5000");
  const [tab, setTab] = useState("customers");

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: FONT_SANS }}>
      <style>{`
        .app-input {
          transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
        }
        .app-input:focus {
          outline: none;
          border-color: ${C.accent} !important;
          box-shadow: 0 0 0 3px ${C.accentSoft};
        }
        .app-search:focus {
          background: #ffffff;
          box-shadow: 0 0 0 3px ${C.hoverBg};
        }
        .app-table tbody tr:nth-child(even) {
          background: ${C.stripe};
        }
        .app-table tbody tr:hover {
          background: ${C.hoverBg};
        }
      `}</style>
      <div style={{ maxWidth: 1040, margin: "0 auto", padding: "28px 20px 60px" }}>
        <header style={{ display: "flex", justifyContent: "flex-end", alignItems: "flex-end", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
          <Field label="API address">
            <TextInput
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              placeholder="http://localhost:5000"
              style={{ width: 220, fontFamily: FONT_MONO, fontSize: 12.5 }}
            />
          </Field>
        </header>

        <nav
          style={{
            display: "flex",
            gap: 4,
            borderBottom: `1px solid ${C.line}`,
            marginBottom: 24,
            paddingBottom: 0,
            flexWrap: "wrap",
          }}
        >
          {TABS.map((t) => {
            const isActive = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                style={{
                  fontFamily: FONT_SANS,
                  fontSize: 13,
                  fontWeight: isActive ? 700 : 500,
                  padding: "9px 14px",
                  background: "none",
                  border: "none",
                  borderBottom: isActive ? `2px solid ${C.blue}` : "2px solid transparent",
                  marginBottom: -1,
                  color: isActive ? C.blue : C.inkFaint,
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            );
          })}
        </nav>

        <main>
          {tab === "customers" && <CustomersPanel apiBase={apiBase} active={tab === "customers"} />}
          {tab === "products" && <ProductsPanel apiBase={apiBase} active={tab === "products"} />}
          {tab === "priceLists" && <PriceListsPanel apiBase={apiBase} active={tab === "priceLists"} />}
          {tab === "priceListItems" && <PriceListItemsPanel apiBase={apiBase} active={tab === "priceListItems"} />}
          {tab === "receipts" && <ReceiptsPanel apiBase={apiBase} active={tab === "receipts"} />}
        </main>
      </div>
    </div>
  );
}
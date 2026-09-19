import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";

/* ---------------------------------------------------------------------
   Design tokens — white body, baby-blue accent throughout: tables,
   focus rings, and the search box all pick up the same soft blue.
--------------------------------------------------------------------- */
const FONT_MONO = "'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace";
const FONT_SANS =
  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

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

// Shown at the top-left of the page. Change this to your system's name.
const APP_NAME = "Sales & Inventory";

const TABS = [
  { key: "customers", label: "Customers" },
  { key: "products", label: "Products" },
  { key: "priceLists", label: "Price Lists" },
  { key: "priceListItems", label: "Price List Items" },
  { key: "receipts", label: "Receipts" },
  { key: "returns", label: "Returns" },
];

const PAGE_SIZE = 10;
// How many rows to ask for per request while loading a full list.
const FETCH_LIMIT = 500;

const STATUS_LABELS = {
  COMPLETED: "Completed",
  PARTIALLY_RETURNED: "Partially returned",
  FULLY_RETURNED: "Fully returned",
};

/* ---------------------------------------------------------------------
   Data hook — loads EVERY row of a list endpoint by walking through
   all of the API's pages, so search and filters can work across the
   whole dataset instead of just the page on screen. Paging in the UI
   is done locally (see usePaged).
--------------------------------------------------------------------- */
function useAllRows(apiBase, path, active) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!active) return undefined;
    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const all = [];
        let page = 1;
        let total = Infinity;
        while (all.length < total) {
          const res = await fetch(
            `${apiBase}${path}?page=${page}&limit=${FETCH_LIMIT}`,
          );
          const body = await res.json().catch(() => null);
          if (!res.ok)
            throw new Error(
              (body && body.message) || `Couldn't load ${path} (${res.status})`,
            );
          // Backend wraps list responses as { data, page, limit, total },
          // but tolerate a bare array too.
          const list = Array.isArray(body)
            ? body
            : Array.isArray(body?.data)
              ? body.data
              : [];
          all.push(...list);
          if (Array.isArray(body) || typeof body?.total !== "number") break;
          total = body.total;
          if (list.length === 0) break;
          page += 1;
        }
        if (!cancelled) setData(all);
      } catch (err) {
        if (cancelled) return;
        // Surface network-level failures ("Failed to fetch") distinctly from
        // API error responses, since the fix for each is different.
        if (err instanceof TypeError) {
          setError(
            `Couldn't reach the server at ${apiBase}. Check that the API is running and reachable.`,
          );
        } else {
          setError(err.message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [apiBase, path, active, tick]);

  return { data, loading, error, reload, setError };
}

/* Client-side paging over an already-filtered list. Jumps back to
   page 1 whenever `resetKey` changes (search text or filters). */
function usePaged(rows, resetKey) {
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [resetKey]);
  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageRows = rows.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  return { page: safePage, setPage, pageRows };
}

/* Prev/Next pager. `page` is 1-based; `total` is the number of rows
   that match the current search and filters. */
function Pagination({ page, onChange, limit, total }) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  if (totalPages <= 1) return null;
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        gap: 10,
        marginTop: 10,
        fontFamily: FONT_SANS,
      }}
    >
      <Btn
        variant="ghost"
        onClick={() => onChange(Math.max(1, page - 1))}
        disabled={page <= 1}
      >
        Previous
      </Btn>
      <span style={{ fontSize: 12.5, color: C.inkFaint }}>
        Page {page} of {totalPages}
      </span>
      <Btn
        variant="ghost"
        onClick={() => onChange(Math.min(totalPages, page + 1))}
        disabled={page >= totalPages}
      >
        Next
      </Btn>
    </div>
  );
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
    throw new Error(
      `Couldn't reach the server at ${apiBase}. Check that the API is running and reachable.`,
    );
  }
  let parsed = null;
  try {
    parsed = await res.json();
  } catch (e) {
    /* no body */
  }
  if (!res.ok) {
    throw new Error(
      (parsed && parsed.message) || `Request failed (${res.status})`,
    );
  }
  return parsed;
}

/* ---------------------------------------------------------------------
   Search + filter helpers
--------------------------------------------------------------------- */

/* Every primitive value in a row, including nested objects and arrays
   (e.g. receipt items), so search covers any field the API returns. */
function collectValues(v, out = []) {
  if (v === null || v === undefined) return out;
  if (Array.isArray(v)) v.forEach((x) => collectValues(x, out));
  else if (typeof v === "object")
    Object.values(v).forEach((x) => collectValues(x, out));
  else out.push(v);
  return out;
}

/* Every space-separated word must appear somewhere in the row (in any
   field, in any order). `fields` can be values, arrays, or nested arrays. */
function searchMatch(search, ...fields) {
  const tokens = search.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return true;
  const haystack = fields
    .flat(Infinity)
    .map((f) => String(f ?? "").toLowerCase())
    .join("\u0001");
  return tokens.every((t) => haystack.includes(t));
}

function inNumberRange(value, from, to) {
  const n = Number(value);
  if (from !== "" && !(n >= Number(from))) return false;
  if (to !== "" && !(n <= Number(to))) return false;
  return true;
}

/* Normalises API dates ("2025-03-04", "2025-03-04T10:15:00", or anything
   Date can parse) to a YYYY-MM-DD key for comparing against date inputs. */
function dateKey(value) {
  if (!value) return "";
  const s = String(value);
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function inDateRange(value, from, to) {
  if (!from && !to) return true;
  const k = dateKey(value);
  if (!k) return false;
  if (from && k < from) return false;
  if (to && k > to) return false;
  return true;
}

function countActive(filters) {
  return Object.values(filters).filter((v) => v !== "").length;
}

function emptyText({ loading, all, shown, noun, hint }) {
  if (loading && all === 0) return "Loading…";
  if (all === 0) return `No ${noun} yet — ${hint}`;
  if (shown === 0) return `No ${noun} match your search or filters.`;
  return null;
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
    <label
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        fontFamily: FONT_SANS,
      }}
    >
      <span style={{ fontSize: 11.5, color: C.inkFaint, letterSpacing: 0.2 }}>
        {label}
      </span>
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
  return (
    <input
      {...props}
      className={`app-input ${className || ""}`}
      style={{ ...inputStyle, ...(props.style || {}) }}
    />
  );
}

function Select({ children, className, ...props }) {
  return (
    <select
      {...props}
      className={`app-input ${className || ""}`}
      style={{ ...inputStyle, ...(props.style || {}) }}
    >
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
    ghost: {
      background: "transparent",
      color: C.ink,
      border: `1px solid ${C.line}`,
    },
    danger: {
      background: "transparent",
      color: C.danger,
      border: `1px solid ${C.danger}55`,
    },
  };
  return (
    <button {...props} style={{ ...base, ...variants[variant], ...style }} />
  );
}

/* Search box. The text is matched against every field of every row
   (across all pages) by the panel that owns it. Styled as a filled
   blue pill with a search icon so it reads as its own thing rather
   than blending into the form fields above. */
function SearchInput({ value, onChange, placeholder }) {
  return (
    <div style={{ position: "relative", width: 300, maxWidth: "100%" }}>
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
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </span>
      <input
        className="app-input app-search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
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

function Toolbar({ search, onSearch, placeholder, shown, total, children }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 12,
        gap: 12,
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <SearchInput
          value={search}
          onChange={onSearch}
          placeholder={placeholder}
        />
        {children}
      </div>
      <span style={{ fontSize: 12, color: C.inkFaint, fontFamily: FONT_SANS }}>
        {shown} of {total}
      </span>
    </div>
  );
}

/* Filter icon that sits beside the search box and opens a small popover
   with the panel's filter controls. A badge on the icon shows how many
   filters are set. Closes on outside click or Escape. */
function Filters({ children, activeCount, onClear }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const hasActive = activeCount > 0;

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={hasActive ? `Filters (${activeCount} active)` : "Filters"}
        aria-expanded={open}
        title="Filters"
        style={{
          position: "relative",
          width: 36,
          height: 36,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 999,
          cursor: "pointer",
          border: `1.5px solid ${hasActive || open ? C.accent : C.accentSoft}`,
          background: hasActive ? C.accent : C.accentSoft,
          color: hasActive ? "#fff" : C.accentText,
          padding: 0,
        }}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
        </svg>
        {hasActive && (
          <span
            style={{
              position: "absolute",
              top: -5,
              right: -5,
              minWidth: 16,
              height: 16,
              padding: "0 4px",
              boxSizing: "border-box",
              borderRadius: 999,
              background: C.blue,
              color: "#fff",
              border: "2px solid #fff",
              fontFamily: FONT_SANS,
              fontSize: 10,
              fontWeight: 700,
              lineHeight: "12px",
              textAlign: "center",
            }}
          >
            {activeCount}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Filters"
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            left: 0,
            zIndex: 30,
            width: 300,
            maxWidth: "calc(100vw - 40px)",
            boxSizing: "border-box",
            background: C.card,
            border: `1px solid ${C.line}`,
            borderRadius: 8,
            padding: 14,
            boxShadow: "0 8px 24px rgba(24, 24, 27, 0.10)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 12,
            }}
          >
            <span
              style={{
                fontFamily: FONT_SANS,
                fontSize: 13,
                fontWeight: 600,
                color: C.ink,
              }}
            >
              Filters
            </span>
            <Btn
              type="button"
              variant="ghost"
              onClick={onClear}
              disabled={!hasActive}
              style={{
                padding: "3px 10px",
                fontSize: 12,
                opacity: hasActive ? 1 : 0.5,
                cursor: hasActive ? "pointer" : "default",
              }}
            >
              Clear all
            </Btn>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {children}
          </div>
        </div>
      )}
    </div>
  );
}

/* A "from – to" pair of inputs, for numbers or dates. */
function RangeField({ label, type = "number", from, to, onFrom, onTo }) {
  const isNumber = type === "number";
  const inputProps = {
    type,
    min: isNumber ? "0" : undefined,
    style: { flex: 1, minWidth: 0 },
  };
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        fontFamily: FONT_SANS,
      }}
    >
      <span style={{ fontSize: 11.5, color: C.inkFaint, letterSpacing: 0.2 }}>
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <TextInput
          {...inputProps}
          aria-label={`${label}, from`}
          placeholder={isNumber ? "Min" : undefined}
          value={from}
          onChange={(e) => onFrom(e.target.value)}
        />
        <span style={{ color: C.inkFaint }}>–</span>
        <TextInput
          {...inputProps}
          aria-label={`${label}, to`}
          placeholder={isNumber ? "Max" : undefined}
          value={to}
          onChange={(e) => onTo(e.target.value)}
        />
      </div>
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
    <div
      style={{
        overflowX: "auto",
        border: `1px solid ${C.line}`,
        borderRadius: 6,
      }}
    >
      <table
        className="app-table"
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontFamily: FONT_SANS,
          tableLayout: "fixed",
        }}
      >
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
        <div
          style={{
            padding: "22px 14px",
            textAlign: "center",
            color: C.inkFaint,
            fontSize: 13,
            fontFamily: FONT_SANS,
          }}
        >
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
        <h2
          style={{
            fontFamily: FONT_SANS,
            fontWeight: 600,
            fontSize: 19,
            margin: 0,
            color: C.ink,
          }}
        >
          {title}
        </h2>
        {subtitle && (
          <p
            style={{
              margin: "4px 0 0",
              color: C.inkFaint,
              fontSize: 13,
              fontFamily: FONT_SANS,
            }}
          >
            {subtitle}
          </p>
        )}
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

function StatusBadge({ status }) {
  const styles = {
    COMPLETED: { bg: C.accentSoft, fg: C.accentText },
    PARTIALLY_RETURNED: { bg: "#FFF6E5", fg: "#9A6B00" },
    FULLY_RETURNED: { bg: C.dangerSoft, fg: C.danger },
  };
  const s = styles[status] || { bg: C.surface, fg: C.inkFaint };
  return (
    <span
      style={{
        fontFamily: FONT_SANS,
        fontSize: 12,
        padding: "2px 8px",
        borderRadius: 3,
        background: s.bg,
        color: s.fg,
      }}
    >
      {STATUS_LABELS[status] || status || "—"}
    </span>
  );
}

/* ---------------------------------------------------------------------
   Customers
--------------------------------------------------------------------- */
const EMPTY_CUSTOMER_FILTERS = { price_list_id: "" };

function CustomersPanel({ apiBase, active }) {
  const {
    data: customers,
    loading,
    error,
    reload,
    setError,
  } = useAllRows(apiBase, "/customers", active);
  const { data: priceLists } = useAllRows(apiBase, "/price-list", active);

  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_CUSTOMER_FILTERS);
  const setF = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const [form, setForm] = useState({ name: "", price_list_id: "" });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", price_list_id: "" });
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

  const priceListById = useMemo(
    () => new Map(priceLists.map((p) => [p.price_list_id, p])),
    [priceLists],
  );
  const priceListLabel = (id) =>
    priceListById.get(id)?.price_list_type ?? `#${id}`;

  const filtered = useMemo(
    () =>
      customers.filter((c) => {
        if (
          filters.price_list_id &&
          String(c.price_list_id) !== filters.price_list_id
        )
          return false;
        return searchMatch(
          search,
          collectValues(c),
          priceListLabel(c.price_list_id),
        );
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [customers, priceListById, search, filters],
  );
  const { page, setPage, pageRows } = usePaged(
    filtered,
    JSON.stringify([search, filters]),
  );

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
    <Panel
      title="Customers"
      subtitle="Who you sell to, and the price list each one shops from."
    >
      <Banner tone="error" onDismiss={() => setError(null)}>
        {error}
      </Banner>
      <Banner tone="ok" onDismiss={() => setNotice(null)}>
        {notice}
      </Banner>

      <SectionCard>
        <form
          onSubmit={handleAdd}
          style={{
            display: "flex",
            gap: 12,
            alignItems: "flex-end",
            flexWrap: "wrap",
          }}
        >
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
              onChange={(e) =>
                setForm({ ...form, price_list_id: e.target.value })
              }
            >
              <option value="" disabled>
                Choose one
              </option>
              {priceLists.map((p) => (
                <option key={p.price_list_id} value={p.price_list_id}>
                  {p.price_list_type}
                </option>
              ))}
            </Select>
          </Field>
          <Btn type="submit" disabled={busy}>
            Add customer
          </Btn>
        </form>
      </SectionCard>

      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search customers..."
        shown={filtered.length}
        total={customers.length}
      >
        <Filters
          activeCount={countActive(filters)}
          onClear={() => setFilters(EMPTY_CUSTOMER_FILTERS)}
        >
          <Field label="Price list">
            <Select
              value={filters.price_list_id}
              onChange={(e) => setF({ price_list_id: e.target.value })}
            >
              <option value="">All</option>
              {priceLists.map((p) => (
                <option key={p.price_list_id} value={p.price_list_id}>
                  {p.price_list_type}
                </option>
              ))}
            </Select>
          </Field>
        </Filters>
      </Toolbar>

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Name", align: "left" },
          { label: "Price list", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={emptyText({
          loading,
          all: customers.length,
          shown: filtered.length,
          noun: "customers",
          hint: "add one above.",
        })}
      >
        {pageRows.map((c) => {
          const isEditing = editingId === c.customer_id;
          return (
            <tr key={c.customer_id}>
              <Td mono align="right">
                {c.customer_id}
              </Td>
              <Td>
                {isEditing ? (
                  <TextInput
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                  />
                ) : (
                  c.name
                )}
              </Td>
              <Td>
                {isEditing ? (
                  <Select
                    value={editForm.price_list_id}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        price_list_id: e.target.value,
                      })
                    }
                  >
                    {priceLists.map((p) => (
                      <option key={p.price_list_id} value={p.price_list_id}>
                        {p.price_list_type}
                      </option>
                    ))}
                  </Select>
                ) : (
                  priceListLabel(c.price_list_id)
                )}
              </Td>
              <Td align="right" width={160}>
                {isEditing ? (
                  <div
                    style={{
                      display: "flex",
                      gap: 6,
                      justifyContent: "flex-end",
                    }}
                  >
                    <Btn
                      variant="primary"
                      onClick={() => saveEdit(c.customer_id)}
                      disabled={busy}
                    >
                      Save
                    </Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>
                      Cancel
                    </Btn>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      gap: 6,
                      justifyContent: "flex-end",
                    }}
                  >
                    <Btn variant="ghost" onClick={() => startEdit(c)}>
                      Edit
                    </Btn>
                    <Btn
                      variant="danger"
                      onClick={() => handleDelete(c.customer_id)}
                    >
                      Delete
                    </Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
      <Pagination
        page={page}
        onChange={setPage}
        limit={PAGE_SIZE}
        total={filtered.length}
      />
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Products
--------------------------------------------------------------------- */
const EMPTY_PRODUCT_FILTERS = { status: "", stockFrom: "", stockTo: "" };

function ProductsPanel({ apiBase, active }) {
  const {
    data: products,
    loading,
    error,
    reload,
    setError,
  } = useAllRows(apiBase, "/products", active);

  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_PRODUCT_FILTERS);
  const setF = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const [form, setForm] = useState({ name: "", stock: "" });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({
    name: "",
    stock: "",
    is_active: 1,
  });
  const [busy, setBusy] = useState(false);

  const filtered = useMemo(
    () =>
      products.filter((p) => {
        if (
          filters.status !== "" &&
          String(Number(p.is_active)) !== filters.status
        )
          return false;
        if (!inNumberRange(p.stock, filters.stockFrom, filters.stockTo))
          return false;
        return searchMatch(
          search,
          collectValues(p),
          p.is_active ? "Active" : "Inactive",
        );
      }),
    [products, search, filters],
  );
  const { page, setPage, pageRows } = usePaged(
    filtered,
    JSON.stringify([search, filters]),
  );

  async function handleAdd(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, "/products", "POST", {
        name: form.name,
        stock: Number(form.stock),
      });
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
    setEditForm({
      name: p.name,
      stock: String(p.stock),
      is_active: p.is_active,
    });
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
    if (
      !window.confirm(
        "Delete this product? If it's used in past receipts, deactivate it instead.",
      )
    )
      return;
    setError(null);
    try {
      await send(apiBase, `/products/${id}`, "DELETE");
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel
      title="Products"
      subtitle="Stock on hand and whether an item can still be sold."
    >
      <Banner tone="error" onDismiss={() => setError(null)}>
        {error}
      </Banner>

      <SectionCard>
        <form
          onSubmit={handleAdd}
          style={{
            display: "flex",
            gap: 12,
            alignItems: "flex-end",
            flexWrap: "wrap",
          }}
        >
          <Field label="Name">
            <TextInput
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Pen"
            />
          </Field>
          <Field label="Stock">
            <TextInput
              required
              type="number"
              min="0"
              value={form.stock}
              onChange={(e) => setForm({ ...form, stock: e.target.value })}
            />
          </Field>
          <Btn type="submit" disabled={busy}>
            Add product
          </Btn>
        </form>
      </SectionCard>

      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search products..."
        shown={filtered.length}
        total={products.length}
      >
        <Filters
          activeCount={countActive(filters)}
          onClear={() => setFilters(EMPTY_PRODUCT_FILTERS)}
        >
          <Field label="Status">
            <Select
              value={filters.status}
              onChange={(e) => setF({ status: e.target.value })}
            >
              <option value="">All</option>
              <option value="1">Active</option>
              <option value="0">Inactive</option>
            </Select>
          </Field>
          <RangeField
            label="Stock"
            from={filters.stockFrom}
            to={filters.stockTo}
            onFrom={(v) => setF({ stockFrom: v })}
            onTo={(v) => setF({ stockTo: v })}
          />
        </Filters>
      </Toolbar>

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Name", align: "left" },
          { label: "Stock", align: "right" },
          { label: "Active", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={emptyText({
          loading,
          all: products.length,
          shown: filtered.length,
          noun: "products",
          hint: "add one above.",
        })}
      >
        {pageRows.map((p) => {
          const isEditing = editingId === p.product_id;
          return (
            <tr key={p.product_id}>
              <Td mono align="right">
                {p.product_id}
              </Td>
              <Td>
                {isEditing ? (
                  <TextInput
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                  />
                ) : (
                  p.name
                )}
              </Td>
              <Td mono align="right">
                {isEditing ? (
                  <TextInput
                    type="number"
                    min="0"
                    style={{ width: 90 }}
                    value={editForm.stock}
                    onChange={(e) =>
                      setEditForm({ ...editForm, stock: e.target.value })
                    }
                  />
                ) : (
                  p.stock
                )}
              </Td>
              <Td>
                {isEditing ? (
                  <Select
                    value={editForm.is_active}
                    onChange={(e) =>
                      setEditForm({ ...editForm, is_active: e.target.value })
                    }
                  >
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
                  <div
                    style={{
                      display: "flex",
                      gap: 6,
                      justifyContent: "flex-end",
                    }}
                  >
                    <Btn onClick={() => saveEdit(p.product_id)} disabled={busy}>
                      Save
                    </Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>
                      Cancel
                    </Btn>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      gap: 6,
                      justifyContent: "flex-end",
                    }}
                  >
                    <Btn variant="ghost" onClick={() => startEdit(p)}>
                      Edit
                    </Btn>
                    <Btn
                      variant="danger"
                      onClick={() => handleDelete(p.product_id)}
                    >
                      Delete
                    </Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
      <Pagination
        page={page}
        onChange={setPage}
        limit={PAGE_SIZE}
        total={filtered.length}
      />
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Price Lists
--------------------------------------------------------------------- */
const EMPTY_PRICE_LIST_FILTERS = { usage: "" };

function PriceListsPanel({ apiBase, active }) {
  const {
    data: lists,
    loading,
    error,
    reload,
    setError,
  } = useAllRows(apiBase, "/price-list", active);
  // Used by the "In use / Unused" filter.
  const { data: customers } = useAllRows(apiBase, "/customers", active);

  const [form, setForm] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [replacementId, setReplacementId] = useState("");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_PRICE_LIST_FILTERS);
  const setF = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const usedIds = useMemo(
    () => new Set(customers.map((c) => c.price_list_id)),
    [customers],
  );

  const filtered = useMemo(
    () =>
      lists.filter((pl) => {
        if (filters.usage === "used" && !usedIds.has(pl.price_list_id))
          return false;
        if (filters.usage === "unused" && usedIds.has(pl.price_list_id))
          return false;
        return searchMatch(search, collectValues(pl));
      }),
    [lists, usedIds, search, filters],
  );
  const { page, setPage, pageRows } = usePaged(
    filtered,
    JSON.stringify([search, filters]),
  );

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
      await send(apiBase, `/price-list/${id}`, "PUT", {
        price_list_type: editValue,
      });
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function startDelete(id) {
    setDeletingId(id);
    setReplacementId("");
  }

  async function confirmDelete(id) {
    if (!replacementId) return;
    setBusy(true);
    setError(null);
    try {
      await send(apiBase, `/price-list/${id}`, "DELETE", {
        replacement_price_list_id: Number(replacementId),
      });
      setDeletingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel
      title="Price Lists"
      subtitle="Named tiers — Retail, Wholesale, and so on — that customers are assigned to."
    >
      <Banner tone="error" onDismiss={() => setError(null)}>
        {error}
      </Banner>

      <SectionCard>
        <form
          onSubmit={handleAdd}
          style={{ display: "flex", gap: 12, alignItems: "flex-end" }}
        >
          <Field label="Price list name">
            <TextInput
              required
              value={form}
              onChange={(e) => setForm(e.target.value)}
              placeholder="e.g. Wholesale"
            />
          </Field>
          <Btn type="submit" disabled={busy}>
            Add price list
          </Btn>
        </form>
      </SectionCard>

      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search price lists..."
        shown={filtered.length}
        total={lists.length}
      >
        <Filters
          activeCount={countActive(filters)}
          onClear={() => setFilters(EMPTY_PRICE_LIST_FILTERS)}
        >
          <Field label="Usage">
            <Select
              value={filters.usage}
              onChange={(e) => setF({ usage: e.target.value })}
            >
              <option value="">All</option>
              <option value="used">Has customers</option>
              <option value="unused">No customers</option>
            </Select>
          </Field>
        </Filters>
      </Toolbar>

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Type", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={emptyText({
          loading,
          all: lists.length,
          shown: filtered.length,
          noun: "price lists",
          hint: "add one above.",
        })}
      >
        {pageRows.map((pl) => {
          const isEditing = editingId === pl.price_list_id;
          const isDeleting = deletingId === pl.price_list_id;
          const otherLists = lists.filter(
            (p) => p.price_list_id !== pl.price_list_id,
          );
          return (
            <React.Fragment key={pl.price_list_id}>
              <tr>
                <Td mono align="right">
                  {pl.price_list_id}
                </Td>
                <Td>
                  {isEditing ? (
                    <TextInput
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                    />
                  ) : (
                    pl.price_list_type
                  )}
                </Td>
                <Td align="right" width={160}>
                  {isEditing ? (
                    <div
                      style={{
                        display: "flex",
                        gap: 6,
                        justifyContent: "flex-end",
                      }}
                    >
                      <Btn
                        onClick={() => saveEdit(pl.price_list_id)}
                        disabled={busy}
                      >
                        Save
                      </Btn>
                      <Btn variant="ghost" onClick={() => setEditingId(null)}>
                        Cancel
                      </Btn>
                    </div>
                  ) : (
                    <div
                      style={{
                        display: "flex",
                        gap: 6,
                        justifyContent: "flex-end",
                      }}
                    >
                      <Btn
                        variant="ghost"
                        onClick={() => {
                          setEditingId(pl.price_list_id);
                          setEditValue(pl.price_list_type);
                        }}
                      >
                        Edit
                      </Btn>
                      <Btn
                        variant="danger"
                        onClick={() => startDelete(pl.price_list_id)}
                        disabled={isDeleting}
                      >
                        Delete
                      </Btn>
                    </div>
                  )}
                </Td>
              </tr>
              {isDeleting && (
                <tr>
                  <Td colSpan={3}>
                    <div
                      style={{
                        display: "flex",
                        gap: 10,
                        alignItems: "flex-end",
                        flexWrap: "wrap",
                        justifyContent: "flex-end",
                      }}
                    >
                      {otherLists.length === 0 ? (
                        <span style={{ fontSize: 13, color: C.inkFaint }}>
                          You need at least one other price list to move its
                          customers to before deleting this one.
                        </span>
                      ) : (
                        <Field label="Move its customers to">
                          <Select
                            value={replacementId}
                            onChange={(e) => setReplacementId(e.target.value)}
                          >
                            <option value="" disabled>
                              Choose a price list
                            </option>
                            {otherLists.map((p) => (
                              <option
                                key={p.price_list_id}
                                value={p.price_list_id}
                              >
                                {p.price_list_type}
                              </option>
                            ))}
                          </Select>
                        </Field>
                      )}
                      <Btn
                        variant="danger"
                        onClick={() => confirmDelete(pl.price_list_id)}
                        disabled={busy || !replacementId}
                      >
                        Confirm delete
                      </Btn>
                      <Btn variant="ghost" onClick={() => setDeletingId(null)}>
                        Cancel
                      </Btn>
                    </div>
                  </Td>
                </tr>
              )}
            </React.Fragment>
          );
        })}
      </Table>
      <Pagination
        page={page}
        onChange={setPage}
        limit={PAGE_SIZE}
        total={filtered.length}
      />
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Price List Items
--------------------------------------------------------------------- */
const EMPTY_ITEM_FILTERS = {
  price_list_id: "",
  product_id: "",
  priceFrom: "",
  priceTo: "",
};

function PriceListItemsPanel({ apiBase, active }) {
  const {
    data: items,
    loading,
    error,
    reload,
    setError,
  } = useAllRows(apiBase, "/price-list-items", active);
  // Also used for the dropdowns and for looking up labels by id.
  const { data: priceLists } = useAllRows(apiBase, "/price-list", active);
  const { data: products } = useAllRows(apiBase, "/products", active);

  const [form, setForm] = useState({
    price_list_id: "",
    product_id: "",
    price: "",
  });
  const [editingId, setEditingId] = useState(null);
  const [editPrice, setEditPrice] = useState("");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_ITEM_FILTERS);
  const setF = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const priceListById = useMemo(
    () => new Map(priceLists.map((p) => [p.price_list_id, p])),
    [priceLists],
  );
  const productById = useMemo(
    () => new Map(products.map((p) => [p.product_id, p])),
    [products],
  );
  const plLabel = (id) => priceListById.get(id)?.price_list_type ?? `#${id}`;
  const prodLabel = (id) => productById.get(id)?.name ?? `#${id}`;

  const filtered = useMemo(
    () =>
      items.filter((it) => {
        if (
          filters.price_list_id &&
          String(it.price_list_id) !== filters.price_list_id
        )
          return false;
        if (filters.product_id && String(it.product_id) !== filters.product_id)
          return false;
        if (!inNumberRange(it.price, filters.priceFrom, filters.priceTo))
          return false;
        return searchMatch(
          search,
          collectValues(it),
          plLabel(it.price_list_id),
          prodLabel(it.product_id),
          money(it.price),
        );
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [items, priceListById, productById, search, filters],
  );
  const { page, setPage, pageRows } = usePaged(
    filtered,
    JSON.stringify([search, filters]),
  );

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
      await send(apiBase, `/price-list-items/${id}`, "PUT", {
        price: Number(editPrice),
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
    <Panel
      title="Price List Items"
      subtitle="What each product costs on each price list."
    >
      <Banner tone="error" onDismiss={() => setError(null)}>
        {error}
      </Banner>

      <SectionCard>
        <form
          onSubmit={handleAdd}
          style={{
            display: "flex",
            gap: 12,
            alignItems: "flex-end",
            flexWrap: "wrap",
          }}
        >
          <Field label="Price list">
            <Select
              required
              value={form.price_list_id}
              onChange={(e) =>
                setForm({ ...form, price_list_id: e.target.value })
              }
            >
              <option value="" disabled>
                Choose one
              </option>
              {priceLists.map((p) => (
                <option key={p.price_list_id} value={p.price_list_id}>
                  {p.price_list_type}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Product">
            <Select
              required
              value={form.product_id}
              onChange={(e) => setForm({ ...form, product_id: e.target.value })}
            >
              <option value="" disabled>
                Choose one
              </option>
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Price">
            <TextInput
              required
              type="number"
              min="0"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
            />
          </Field>
          <Btn type="submit" disabled={busy}>
            Add item
          </Btn>
        </form>
      </SectionCard>

      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search price list items..."
        shown={filtered.length}
        total={items.length}
      >
        <Filters
          activeCount={countActive(filters)}
          onClear={() => setFilters(EMPTY_ITEM_FILTERS)}
        >
          <Field label="Price list">
            <Select
              value={filters.price_list_id}
              onChange={(e) => setF({ price_list_id: e.target.value })}
            >
              <option value="">All</option>
              {priceLists.map((p) => (
                <option key={p.price_list_id} value={p.price_list_id}>
                  {p.price_list_type}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Product">
            <Select
              value={filters.product_id}
              onChange={(e) => setF({ product_id: e.target.value })}
            >
              <option value="">All</option>
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </Field>
          <RangeField
            label="Price"
            from={filters.priceFrom}
            to={filters.priceTo}
            onFrom={(v) => setF({ priceFrom: v })}
            onTo={(v) => setF({ priceTo: v })}
          />
        </Filters>
      </Toolbar>

      <Table
        columns={[
          { label: "ID", align: "right" },
          { label: "Price list", align: "left" },
          { label: "Product", align: "left" },
          { label: "Price", align: "right" },
          { label: "", align: "right" },
        ]}
        empty={emptyText({
          loading,
          all: items.length,
          shown: filtered.length,
          noun: "price list items",
          hint: "add one above.",
        })}
      >
        {pageRows.map((it) => {
          const isEditing = editingId === it.id;
          return (
            <tr key={it.id}>
              <Td mono align="right">
                {it.id}
              </Td>
              <Td>{plLabel(it.price_list_id)}</Td>
              <Td>{prodLabel(it.product_id)}</Td>
              <Td mono align="right">
                {isEditing ? (
                  <TextInput
                    type="number"
                    min="0"
                    style={{ width: 90 }}
                    value={editPrice}
                    onChange={(e) => setEditPrice(e.target.value)}
                  />
                ) : (
                  money(it.price)
                )}
              </Td>
              <Td align="right" width={160}>
                {isEditing ? (
                  <div
                    style={{
                      display: "flex",
                      gap: 6,
                      justifyContent: "flex-end",
                    }}
                  >
                    <Btn onClick={() => saveEdit(it.id)} disabled={busy}>
                      Save
                    </Btn>
                    <Btn variant="ghost" onClick={() => setEditingId(null)}>
                      Cancel
                    </Btn>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      gap: 6,
                      justifyContent: "flex-end",
                    }}
                  >
                    <Btn
                      variant="ghost"
                      onClick={() => {
                        setEditingId(it.id);
                        setEditPrice(String(it.price));
                      }}
                    >
                      Edit
                    </Btn>
                    <Btn variant="danger" onClick={() => handleDelete(it.id)}>
                      Delete
                    </Btn>
                  </div>
                )}
              </Td>
            </tr>
          );
        })}
      </Table>
      <Pagination
        page={page}
        onChange={setPage}
        limit={PAGE_SIZE}
        total={filtered.length}
      />
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Receipts
--------------------------------------------------------------------- */
const EMPTY_RECEIPT_FILTERS = {
  customer_id: "",
  status: "",
  product_id: "",
  dateFrom: "",
  dateTo: "",
  totalFrom: "",
  totalTo: "",
};

function ReceiptsPanel({ apiBase, active }) {
  const {
    data: receipts,
    loading,
    error,
    reload,
    setError,
  } = useAllRows(apiBase, "/receipts", active);
  const { data: customers } = useAllRows(apiBase, "/customers", active);
  const { data: products } = useAllRows(apiBase, "/products", active);

  const [customerId, setCustomerId] = useState("");
  const [lines, setLines] = useState([{ product_id: "", quantity: "1" }]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [openId, setOpenId] = useState(null);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_RECEIPT_FILTERS);
  const setF = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const customerById = useMemo(
    () => new Map(customers.map((c) => [c.customer_id, c])),
    [customers],
  );
  const productById = useMemo(
    () => new Map(products.map((p) => [p.product_id, p])),
    [products],
  );
  const customerLabel = (id) => customerById.get(id)?.name ?? `#${id}`;
  const productLabel = (id) => productById.get(id)?.name ?? `#${id}`;

  const filtered = useMemo(
    () =>
      receipts.filter((r) => {
        if (
          filters.customer_id &&
          String(r.customer_id) !== filters.customer_id
        )
          return false;
        if (filters.status && r.status !== filters.status) return false;
        if (
          filters.product_id &&
          !(r.items || []).some(
            (it) => String(it.product_id) === filters.product_id,
          )
        )
          return false;
        if (!inDateRange(r.date, filters.dateFrom, filters.dateTo))
          return false;
        if (!inNumberRange(r.total, filters.totalFrom, filters.totalTo))
          return false;
        return searchMatch(
          search,
          collectValues(r),
          customerLabel(r.customer_id),
          (r.items || []).map((it) => productLabel(it.product_id)),
          STATUS_LABELS[r.status],
          money(r.total),
        );
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [receipts, customerById, productById, search, filters],
  );
  const { page, setPage, pageRows } = usePaged(
    filtered,
    JSON.stringify([search, filters]),
  );

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
        .map((l) => ({
          product_id: Number(l.product_id),
          quantity: Number(l.quantity),
        }));
      if (items.length === 0)
        throw new Error("Add at least one item to the receipt.");
      await send(apiBase, "/receipts", "POST", {
        customer_id: Number(customerId),
        items,
      });
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
    <Panel
      title="Receipts"
      subtitle="Sales, priced from the customer's own price list and deducted from stock."
    >
      <Banner tone="error" onDismiss={() => setError(null)}>
        {error}
      </Banner>
      <Banner tone="ok" onDismiss={() => setNotice(null)}>
        {notice}
      </Banner>

      <SectionCard>
        <form onSubmit={handleCreate}>
          <div
            style={{
              display: "flex",
              gap: 12,
              marginBottom: 14,
              flexWrap: "wrap",
            }}
          >
            <Field label="Customer">
              <Select
                required
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
              >
                <option value="" disabled>
                  Choose one
                </option>
                {customers.map((c) => (
                  <option key={c.customer_id} value={c.customer_id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 8,
              marginBottom: 12,
            }}
          >
            {lines.map((l, idx) => (
              <div
                key={idx}
                style={{ display: "flex", gap: 10, alignItems: "flex-end" }}
              >
                <Field label="Product">
                  <Select
                    value={l.product_id}
                    onChange={(e) =>
                      updateLine(idx, { product_id: e.target.value })
                    }
                  >
                    <option value="">Choose one</option>
                    {products.map((p) => (
                      <option key={p.product_id} value={p.product_id}>
                        {p.name} ({p.stock} in stock)
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Quantity">
                  <TextInput
                    type="number"
                    min="1"
                    style={{ width: 90 }}
                    value={l.quantity}
                    onChange={(e) =>
                      updateLine(idx, { quantity: e.target.value })
                    }
                  />
                </Field>
                {lines.length > 1 && (
                  <Btn
                    type="button"
                    variant="danger"
                    onClick={() => removeLine(idx)}
                  >
                    Remove
                  </Btn>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <Btn type="button" variant="ghost" onClick={addLine}>
              Add another item
            </Btn>
            <Btn type="submit" disabled={busy}>
              Create receipt
            </Btn>
          </div>
        </form>
      </SectionCard>

      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search receipts..."
        shown={filtered.length}
        total={receipts.length}
      >
        <Filters
          activeCount={countActive(filters)}
          onClear={() => setFilters(EMPTY_RECEIPT_FILTERS)}
        >
          <Field label="Customer">
            <Select
              value={filters.customer_id}
              onChange={(e) => setF({ customer_id: e.target.value })}
            >
              <option value="">All</option>
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Status">
            <Select
              value={filters.status}
              onChange={(e) => setF({ status: e.target.value })}
            >
              <option value="">All</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Contains product">
            <Select
              value={filters.product_id}
              onChange={(e) => setF({ product_id: e.target.value })}
            >
              <option value="">Any</option>
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </Field>
          <RangeField
            label="Date"
            type="date"
            from={filters.dateFrom}
            to={filters.dateTo}
            onFrom={(v) => setF({ dateFrom: v })}
            onTo={(v) => setF({ dateTo: v })}
          />
          <RangeField
            label="Total"
            from={filters.totalFrom}
            to={filters.totalTo}
            onFrom={(v) => setF({ totalFrom: v })}
            onTo={(v) => setF({ totalTo: v })}
          />
        </Filters>
      </Toolbar>

      <Table
        columns={[
          { label: "Receipt #", align: "right" },
          { label: "Customer", align: "left" },
          { label: "Date", align: "left" },
          { label: "Total", align: "right" },
          { label: "Status", align: "left" },
          { label: "", align: "right" },
        ]}
        empty={emptyText({
          loading,
          all: receipts.length,
          shown: filtered.length,
          noun: "receipts",
          hint: "create one above.",
        })}
      >
        {pageRows.map((r) => {
          const rn = r["receipt#"];
          const isOpen = openId === rn;
          return (
            <React.Fragment key={rn}>
              <tr>
                <Td mono align="right">
                  {rn}
                </Td>
                <Td>{customerLabel(r.customer_id)}</Td>
                <Td mono>{r.date}</Td>
                <Td mono align="right">
                  {money(r.total)}
                </Td>
                <Td>
                  <StatusBadge status={r.status} />
                </Td>
                <Td align="right" width={120}>
                  <Btn
                    variant="ghost"
                    onClick={() => setOpenId(isOpen ? null : rn)}
                  >
                    {isOpen ? "Hide items" : "Show items"}
                  </Btn>
                </Td>
              </tr>
              {isOpen && (
                <tr>
                  <Td colSpan={6}>
                    <div style={{ padding: "6px 4px 10px" }}>
                      <table
                        style={{
                          width: "100%",
                          borderCollapse: "collapse",
                          fontFamily: FONT_SANS,
                        }}
                      >
                        <thead>
                          <tr>
                            <th
                              style={{
                                textAlign: "left",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Item
                            </th>
                            <th
                              style={{
                                textAlign: "right",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Quantity
                            </th>
                            <th
                              style={{
                                textAlign: "right",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Price
                            </th>
                            <th
                              style={{
                                textAlign: "right",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Subtotal
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {(r.items || []).map((it, i) => (
                            <tr key={i}>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                }}
                              >
                                {productLabel(it.product_id)}
                              </td>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                  textAlign: "right",
                                  fontFamily: FONT_MONO,
                                }}
                              >
                                {it.quantity}
                              </td>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                  textAlign: "right",
                                  fontFamily: FONT_MONO,
                                }}
                              >
                                {money(it.price)}
                              </td>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                  textAlign: "right",
                                  fontFamily: FONT_MONO,
                                }}
                              >
                                {money(it.price * it.quantity)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td
                              colSpan={3}
                              style={{
                                padding: "7px 8px",
                                textAlign: "right",
                                fontWeight: 700,
                                color: C.ink,
                                borderTop: `1px solid ${C.line}`,
                              }}
                            >
                              Total
                            </td>
                            <td
                              style={{
                                padding: "7px 8px",
                                textAlign: "right",
                                fontWeight: 700,
                                color: C.ink,
                                fontFamily: FONT_MONO,
                                borderTop: `1px solid ${C.line}`,
                              }}
                            >
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
      <Pagination
        page={page}
        onChange={setPage}
        limit={PAGE_SIZE}
        total={filtered.length}
      />
    </Panel>
  );
}

/* ---------------------------------------------------------------------
   Returns
   Route shape confirmed: GET/POST /returns and GET /returns/<id>,
   with POST taking { receipt_no, items }.
--------------------------------------------------------------------- */
const EMPTY_RETURN_FILTERS = {
  receipt_no: "",
  customer_id: "",
  product_id: "",
  dateFrom: "",
  dateTo: "",
  totalFrom: "",
  totalTo: "",
};

function ReturnsPanel({ apiBase, active }) {
  const {
    data: returns,
    loading,
    error,
    reload,
    setError,
  } = useAllRows(apiBase, "/returns", active);
  const { data: receipts } = useAllRows(apiBase, "/receipts", active);
  const { data: customers } = useAllRows(apiBase, "/customers", active);
  const { data: products } = useAllRows(apiBase, "/products", active);

  const [receiptNo, setReceiptNo] = useState("");
  const [lines, setLines] = useState([{ product_id: "", quantity: "1" }]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [openId, setOpenId] = useState(null);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_RETURN_FILTERS);
  const setF = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const customerById = useMemo(
    () => new Map(customers.map((c) => [c.customer_id, c])),
    [customers],
  );
  const productById = useMemo(
    () => new Map(products.map((p) => [p.product_id, p])),
    [products],
  );
  const receiptByNo = useMemo(
    () => new Map(receipts.map((r) => [Number(r["receipt#"]), r])),
    [receipts],
  );
  const customerLabel = (id) => customerById.get(id)?.name ?? `#${id}`;
  const productLabel = (id) => productById.get(id)?.name ?? `#${id}`;
  // A return doesn't store its customer; it belongs to whoever bought on the receipt.
  const returnCustomerId = (ret) =>
    receiptByNo.get(Number(ret.receipt_no))?.customer_id;

  const selectedReceipt = receiptByNo.get(Number(receiptNo));
  const returnableItems = selectedReceipt?.items || [];

  const filtered = useMemo(
    () =>
      returns.filter((r) => {
        const custId = returnCustomerId(r);
        if (filters.receipt_no && String(r.receipt_no) !== filters.receipt_no)
          return false;
        if (filters.customer_id && String(custId) !== filters.customer_id)
          return false;
        if (
          filters.product_id &&
          !(r.items || []).some(
            (it) => String(it.product_id) === filters.product_id,
          )
        )
          return false;
        if (!inDateRange(r.date, filters.dateFrom, filters.dateTo))
          return false;
        if (!inNumberRange(r.total, filters.totalFrom, filters.totalTo))
          return false;
        return searchMatch(
          search,
          collectValues(r),
          custId !== undefined ? customerLabel(custId) : "",
          (r.items || []).map((it) => productLabel(it.product_id)),
          money(r.total),
        );
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [returns, receiptByNo, customerById, productById, search, filters],
  );
  const { page, setPage, pageRows } = usePaged(
    filtered,
    JSON.stringify([search, filters]),
  );

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
        .map((l) => ({
          product_id: Number(l.product_id),
          quantity: Number(l.quantity),
        }));
      if (!receiptNo) throw new Error("Choose the receipt this return is for.");
      if (items.length === 0)
        throw new Error("Add at least one item to return.");
      await send(apiBase, "/returns", "POST", {
        receipt_no: Number(receiptNo),
        items,
      });
      setReceiptNo("");
      setLines([{ product_id: "", quantity: "1" }]);
      setNotice("Return created.");
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel
      title="Returns"
      subtitle="Refund items from a past receipt and restore them to stock."
    >
      <Banner tone="error" onDismiss={() => setError(null)}>
        {error}
      </Banner>
      <Banner tone="ok" onDismiss={() => setNotice(null)}>
        {notice}
      </Banner>

      <SectionCard>
        <form onSubmit={handleCreate}>
          <div
            style={{
              display: "flex",
              gap: 12,
              marginBottom: 14,
              flexWrap: "wrap",
            }}
          >
            <Field label="Receipt">
              <Select
                required
                value={receiptNo}
                onChange={(e) => {
                  setReceiptNo(e.target.value);
                  setLines([{ product_id: "", quantity: "1" }]);
                }}
              >
                <option value="" disabled>
                  Choose one
                </option>
                {receipts.map((r) => (
                  <option key={r["receipt#"]} value={r["receipt#"]}>
                    #{r["receipt#"]} — {customerLabel(r.customer_id)} —{" "}
                    {money(r.total)}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          {receiptNo && returnableItems.length === 0 && (
            <p style={{ fontSize: 13, color: C.inkFaint, marginBottom: 12 }}>
              This receipt has no items on file.
            </p>
          )}

          {receiptNo && returnableItems.length > 0 && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 8,
                marginBottom: 12,
              }}
            >
              {lines.map((l, idx) => (
                <div
                  key={idx}
                  style={{ display: "flex", gap: 10, alignItems: "flex-end" }}
                >
                  <Field label="Product">
                    <Select
                      value={l.product_id}
                      onChange={(e) =>
                        updateLine(idx, { product_id: e.target.value })
                      }
                    >
                      <option value="">Choose one</option>
                      {returnableItems.map((it) => (
                        <option key={it.product_id} value={it.product_id}>
                          {productLabel(it.product_id)} ({it.quantity} on
                          receipt)
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Quantity">
                    <TextInput
                      type="number"
                      min="1"
                      style={{ width: 90 }}
                      value={l.quantity}
                      onChange={(e) =>
                        updateLine(idx, { quantity: e.target.value })
                      }
                    />
                  </Field>
                  {lines.length > 1 && (
                    <Btn
                      type="button"
                      variant="danger"
                      onClick={() => removeLine(idx)}
                    >
                      Remove
                    </Btn>
                  )}
                </div>
              ))}
            </div>
          )}

          <div style={{ display: "flex", gap: 10 }}>
            <Btn
              type="button"
              variant="ghost"
              onClick={addLine}
              disabled={!receiptNo}
            >
              Add another item
            </Btn>
            <Btn type="submit" disabled={busy || !receiptNo}>
              Create return
            </Btn>
          </div>
        </form>
      </SectionCard>

      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search returns..."
        shown={filtered.length}
        total={returns.length}
      >
        <Filters
          activeCount={countActive(filters)}
          onClear={() => setFilters(EMPTY_RETURN_FILTERS)}
        >
          <Field label="Receipt">
            <Select
              value={filters.receipt_no}
              onChange={(e) => setF({ receipt_no: e.target.value })}
            >
              <option value="">All</option>
              {receipts.map((r) => (
                <option key={r["receipt#"]} value={r["receipt#"]}>
                  #{r["receipt#"]} — {customerLabel(r.customer_id)}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Customer">
            <Select
              value={filters.customer_id}
              onChange={(e) => setF({ customer_id: e.target.value })}
            >
              <option value="">All</option>
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Contains product">
            <Select
              value={filters.product_id}
              onChange={(e) => setF({ product_id: e.target.value })}
            >
              <option value="">Any</option>
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </Field>
          <RangeField
            label="Date"
            type="date"
            from={filters.dateFrom}
            to={filters.dateTo}
            onFrom={(v) => setF({ dateFrom: v })}
            onTo={(v) => setF({ dateTo: v })}
          />
          <RangeField
            label="Total"
            from={filters.totalFrom}
            to={filters.totalTo}
            onFrom={(v) => setF({ totalFrom: v })}
            onTo={(v) => setF({ totalTo: v })}
          />
        </Filters>
      </Toolbar>

      <Table
        columns={[
          { label: "Return #", align: "right" },
          { label: "Receipt #", align: "right" },
          { label: "Date", align: "left" },
          { label: "Total", align: "right" },
          { label: "", align: "right" },
        ]}
        empty={emptyText({
          loading,
          all: returns.length,
          shown: filtered.length,
          noun: "returns",
          hint: "create one above.",
        })}
      >
        {pageRows.map((r) => {
          const isOpen = openId === r.return_id;
          return (
            <React.Fragment key={r.return_id}>
              <tr>
                <Td mono align="right">
                  {r.return_id}
                </Td>
                <Td mono align="right">
                  {r.receipt_no}
                </Td>
                <Td mono>{r.date}</Td>
                <Td mono align="right">
                  {money(r.total)}
                </Td>
                <Td align="right" width={120}>
                  <Btn
                    variant="ghost"
                    onClick={() => setOpenId(isOpen ? null : r.return_id)}
                  >
                    {isOpen ? "Hide items" : "Show items"}
                  </Btn>
                </Td>
              </tr>
              {isOpen && (
                <tr>
                  <Td colSpan={5}>
                    <div style={{ padding: "6px 4px 10px" }}>
                      <table
                        style={{
                          width: "100%",
                          borderCollapse: "collapse",
                          fontFamily: FONT_SANS,
                        }}
                      >
                        <thead>
                          <tr>
                            <th
                              style={{
                                textAlign: "left",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Item
                            </th>
                            <th
                              style={{
                                textAlign: "right",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Quantity
                            </th>
                            <th
                              style={{
                                textAlign: "right",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Price
                            </th>
                            <th
                              style={{
                                textAlign: "right",
                                padding: "4px 8px",
                                fontSize: 11,
                                color: C.accentText,
                                fontWeight: 700,
                              }}
                            >
                              Subtotal
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {(r.items || []).map((it, i) => (
                            <tr key={i}>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                }}
                              >
                                {productLabel(it.product_id)}
                              </td>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                  textAlign: "right",
                                  fontFamily: FONT_MONO,
                                }}
                              >
                                {it.quantity}
                              </td>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                  textAlign: "right",
                                  fontFamily: FONT_MONO,
                                }}
                              >
                                {money(it.price)}
                              </td>
                              <td
                                style={{
                                  padding: "5px 8px",
                                  fontSize: 13,
                                  color: C.ink,
                                  textAlign: "right",
                                  fontFamily: FONT_MONO,
                                }}
                              >
                                {money(it.price * it.quantity)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td
                              colSpan={3}
                              style={{
                                padding: "7px 8px",
                                textAlign: "right",
                                fontWeight: 700,
                                color: C.ink,
                                borderTop: `1px solid ${C.line}`,
                              }}
                            >
                              Total
                            </td>
                            <td
                              style={{
                                padding: "7px 8px",
                                textAlign: "right",
                                fontWeight: 700,
                                color: C.ink,
                                fontFamily: FONT_MONO,
                                borderTop: `1px solid ${C.line}`,
                              }}
                            >
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
      <Pagination
        page={page}
        onChange={setPage}
        limit={PAGE_SIZE}
        total={filtered.length}
      />
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
    <div
      style={{ background: C.bg, minHeight: "100vh", fontFamily: FONT_SANS }}
    >
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
      <div
        style={{ maxWidth: 1040, margin: "0 auto", padding: "28px 20px 60px" }}
      >
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            marginBottom: 20,
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <h1
            style={{
              fontFamily: FONT_SANS,
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: -0.2,
              color: C.ink,
              margin: 0,
              lineHeight: 1.2,
            }}
          >
            {APP_NAME}
          </h1>
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
                  borderBottom: isActive
                    ? `2px solid ${C.blue}`
                    : "2px solid transparent",
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
          {tab === "customers" && (
            <CustomersPanel apiBase={apiBase} active={tab === "customers"} />
          )}
          {tab === "products" && (
            <ProductsPanel apiBase={apiBase} active={tab === "products"} />
          )}
          {tab === "priceLists" && (
            <PriceListsPanel apiBase={apiBase} active={tab === "priceLists"} />
          )}
          {tab === "priceListItems" && (
            <PriceListItemsPanel
              apiBase={apiBase}
              active={tab === "priceListItems"}
            />
          )}
          {tab === "receipts" && (
            <ReceiptsPanel apiBase={apiBase} active={tab === "receipts"} />
          )}
          {tab === "returns" && (
            <ReturnsPanel apiBase={apiBase} active={tab === "returns"} />
          )}
        </main>
      </div>
    </div>
  );
}

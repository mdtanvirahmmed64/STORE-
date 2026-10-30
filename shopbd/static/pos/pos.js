/* ShopBD POS — counter sale screen */
(function () {
  "use strict";
  const P = window.POS;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const BN = "০১২৩৪৫৬৭৮৯";
  const digits = (t) => ((window.I18N || {}).bnDigits ? String(t).replace(/[0-9]/g, (d) => BN[d]) : String(t));
  const money = (n) => digits("৳" + (Math.round(n * 100) / 100).toLocaleString("en-US", { maximumFractionDigits: 2 }));
  const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || "";
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const cart = []; // {key, id, name, sku, price, qty, stock, variations:[{id,label}], image}
  let products = [];
  const STORE_KEY = "pos_cart_" + P.branch;

  // keep an unfinished cart if the page is reloaded
  try { (JSON.parse(localStorage.getItem(STORE_KEY)) || []).forEach((l) => cart.push(l)); } catch (e) {}
  const persist = () => { try { localStorage.setItem(STORE_KEY, JSON.stringify(cart)); } catch (e) {} };

  /* ---------------- product search ---------------- */
  const grid = $("#pos-grid");
  const q = $("#pos-q");
  let timer;

  async function search(term, addExact) {
    try {
      const res = await fetch(P.searchUrl + "?branch=" + P.branch + "&q=" + encodeURIComponent(term));
      const data = await res.json();
      products = data.results;
      render();
      // barcode scanners type the code and press Enter → add the exact SKU match directly
      if (addExact && products.length && products[0].exact) {
        pick(products[0]);
        q.value = "";
        q.focus();
        search("");
      }
    } catch (e) { showError((window.I18N || {}).wrong || "Error"); }
  }

  function render() {
    if (!products.length) { grid.innerHTML = `<div class="empty"><i class="fa-solid fa-box-open"></i><p>${esc(P.t.none)}</p></div>`; return; }
    grid.innerHTML = products.map((p, i) => {
      const out = p.stock <= 0 && !P.sellWithoutStock;
      return `<button type="button" class="pos-item${out ? " is-out" : ""}" data-i="${i}" ${out ? "disabled" : ""}>
        <img src="${esc(p.image)}" alt="" loading="lazy">
        <span class="pi-name">${esc(p.name)}</span>
        <span class="pi-sku">${esc(p.sku || "")}</span>
        <span class="pi-foot"><b>${money(+p.price)}</b>
          <em class="${p.stock <= 0 ? "out" : p.stock <= 5 ? "low" : ""}">${p.stock <= 0 ? esc(P.t.out) : digits(p.stock) + " " + esc(P.t.inStock)}</em></span>
      </button>`;
    }).join("");
  }

  grid.addEventListener("click", (e) => {
    const b = e.target.closest(".pos-item");
    if (b) pick(products[+b.dataset.i]);
  });
  q.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => search(q.value.trim()), 250); });
  q.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); clearTimeout(timer); search(q.value.trim(), true); }
  });

  /* ---------------- variations dialog ---------------- */
  const dlg = $("#var-dialog");
  function pick(p) {
    if (!p.variations.length) return addToCart(p, []);
    const groups = {};
    p.variations.forEach((v) => { (groups[v.kind] = groups[v.kind] || { label: v.kind_label, opts: [] }).opts.push(v); });
    $("#var-title").textContent = p.name;
    $("#var-groups").innerHTML = Object.entries(groups).map(([kind, g]) => `
      <div class="var-group"><span>${esc(g.label)}:</span><div class="var-options">
      ${g.opts.map((v, i) => `<input type="radio" id="pv${v.id}" name="pv_${kind}" value="${v.id}" ${i === 0 ? "checked" : ""}>
        <label for="pv${v.id}">${esc(v.value)}${+v.extra ? " (+" + money(+v.extra) + ")" : ""}</label>`).join("")}
      </div></div>`).join("");
    dlg.onclose = () => {
      if (dlg.returnValue !== "ok") return;
      const chosen = $$("#var-groups input:checked").map((i) => p.variations.find((v) => v.id === +i.value));
      addToCart(p, chosen);
    };
    if (dlg.showModal) dlg.showModal(); else { dlg.returnValue = "ok"; dlg.onclose(); }
  }

  /* ---------------- cart ---------------- */
  function addToCart(p, vars) {
    const ids = vars.map((v) => v.id).sort((a, b) => a - b);
    const key = p.id + ":" + ids.join("-");
    const extra = vars.reduce((s, v) => s + +v.extra, 0);
    const line = cart.find((l) => l.key === key);
    const inCart = cart.filter((l) => l.id === p.id).reduce((s, l) => s + l.qty, 0);
    if (!P.sellWithoutStock && inCart + 1 > p.stock) return showError(P.t.noStock);
    if (line) line.qty += 1;
    else cart.push({ key, id: p.id, name: p.name, sku: p.sku, price: +p.price + extra, qty: 1, stock: p.stock,
                     variations: vars.map((v) => ({ id: v.id, label: v.kind_label + ": " + v.value })), image: p.image });
    hideError();
    drawCart();
  }

  const linesBox = $("#cart-lines");
  function drawCart() {
    if (!cart.length) {
      linesBox.innerHTML = `<div class="cart-empty"><i class="fa-solid fa-barcode"></i><p>${esc(P.t.empty)}</p></div>`;
    } else {
      linesBox.innerHTML = cart.map((l, i) => `
        <div class="cart-line">
          <div class="cl-info"><strong>${esc(l.name)}</strong>
            ${l.variations.length ? `<small>${esc(l.variations.map((v) => v.label).join(", "))}</small>` : ""}
            <small>${money(l.price)} × ${digits(l.qty)}</small></div>
          <div class="qty"><button type="button" data-a="dec" data-i="${i}">−</button>
            <input type="number" min="1" value="${l.qty}" data-i="${i}" aria-label="qty">
            <button type="button" data-a="inc" data-i="${i}">+</button></div>
          <b class="cl-total">${money(l.price * l.qty)}</b>
          <button type="button" class="remove-btn" data-a="del" data-i="${i}" aria-label="${esc(P.t.remove)}"><i class="fa-regular fa-trash-can"></i><span class="x">×</span></button>
        </div>`).join("");
    }
    persist();
    totals();
  }

  linesBox.addEventListener("click", (e) => {
    const b = e.target.closest("[data-a]");
    if (!b) return;
    const l = cart[+b.dataset.i];
    const sameProduct = cart.filter((x) => x.id === l.id).reduce((s, x) => s + x.qty, 0);
    if (b.dataset.a === "inc") {
      if (!P.sellWithoutStock && sameProduct + 1 > l.stock) return showError(P.t.noStock);
      l.qty += 1;
    }
    if (b.dataset.a === "dec") l.qty = Math.max(1, l.qty - 1);
    if (b.dataset.a === "del") cart.splice(+b.dataset.i, 1);
    hideError();
    drawCart();
  });
  linesBox.addEventListener("change", (e) => {
    const inp = e.target.closest("input[data-i]");
    if (!inp) return;
    const l = cart[+inp.dataset.i];
    const others = cart.filter((x) => x.id === l.id && x !== l).reduce((s, x) => s + x.qty, 0);
    let v = Math.max(1, parseInt(inp.value || "1", 10));
    if (!P.sellWithoutStock && v + others > l.stock) { v = Math.max(1, l.stock - others); showError(P.t.noStock); }
    l.qty = v;
    drawCart();
  });
  $("#clear-cart").addEventListener("click", () => { if (cart.length && confirm(P.t.clear)) { cart.length = 0; drawCart(); } });

  /* ---------------- totals & payment ---------------- */
  const discValue = $("#disc-value"), discType = $("#disc-type"), paid = $("#paid");
  let currentTotal = 0;
  function method() { return ($("input[name=pay]:checked") || {}).value || "cash"; }

  function totals() {
    const sub = cart.reduce((s, l) => s + l.price * l.qty, 0);
    let d = parseFloat(discValue.value || "0") || 0;
    if (discType.value === "percent") d = Math.min(d, P.maxDiscount) * sub / 100;
    d = Math.min(Math.max(0, d), sub, sub * P.maxDiscount / 100);
    currentTotal = Math.round((sub - d) * 100) / 100;
    $("#t-subtotal").textContent = money(sub);
    $("#t-total").textContent = money(currentTotal);
    const count = cart.reduce((s, l) => s + l.qty, 0);
    $("#cart-count").textContent = digits(count);
    $("#jump-count").textContent = digits(count);
    $("#jump-total").textContent = money(currentTotal);
    const isCash = method() === "cash";
    $("#cash-box").classList.toggle("hidden", !isCash);
    $("#trx-box").classList.toggle("hidden", isCash);
    const p = parseFloat(paid.value || "0") || 0;
    $("#t-change").textContent = money(Math.max(0, p - currentTotal));
    $("#complete").disabled = !cart.length;
  }
  [discValue, discType, paid].forEach((el) => el.addEventListener("input", totals));
  $$("input[name=pay]").forEach((r) => r.addEventListener("change", totals));
  $$("[data-paid]").forEach((b) => b.addEventListener("click", () => {
    paid.value = b.dataset.paid === "exact" ? currentTotal : b.dataset.paid;
    totals();
  }));

  /* ---------------- complete sale ---------------- */
  const errBox = $("#pos-error");
  function showError(msg) { errBox.textContent = msg; errBox.classList.remove("hidden"); if (window.shopToast) window.shopToast(msg, "error"); }
  function hideError() { errBox.classList.add("hidden"); }

  async function complete() {
    if (!cart.length) return;
    const pm = method();
    if (pm === "cash" && paid.value !== "" && parseFloat(paid.value) < currentTotal) return showError(P.t.lessPaid);
    const btn = $("#complete");
    const label = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = P.t.saving;
    try {
      const res = await fetch(P.saleUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify({
          branch: P.branch,
          items: cart.map((l) => ({ product_id: l.id, quantity: l.qty, variation_ids: l.variations.map((v) => v.id) })),
          discount_type: discType.value, discount_value: discValue.value || 0,
          payment_method: pm, paid_amount: pm === "cash" && paid.value !== "" ? paid.value : currentTotal,
          transaction_id: $("#trx").value, customer_name: $("#c-name").value, customer_phone: $("#c-phone").value,
          note: $("#note").value,
        }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Error");
      cart.length = 0;
      persist();
      window.location.href = data.receipt_url;
    } catch (e) {
      showError(e.message);
      btn.disabled = false;
      btn.innerHTML = label;
    }
  }
  $("#complete").addEventListener("click", complete);

  /* ---------------- keyboard shortcuts ---------------- */
  document.addEventListener("keydown", (e) => {
    if (e.key === "F2") { e.preventDefault(); q.focus(); q.select(); }
    if (e.key === "F9") { e.preventDefault(); complete(); }
  });

  drawCart();
  search("");
})();

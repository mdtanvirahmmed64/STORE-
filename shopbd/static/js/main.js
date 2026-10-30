/* ShopBD - main JavaScript (no framework needed) */
(function () {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m.pop()) : "";
  }
  const T = window.I18N || { endsIn: "Ends in", wrong: "Something went wrong.", free: "Free", close: "Close", bnDigits: false };
  const BN = "০১২৩৪৫৬৭৮৯";
  const localDigits = (txt) => (T.bnDigits ? String(txt).replace(/[0-9]/g, (d) => BN[d]) : String(txt));
  window.shopLocalDigits = localDigits;

  const csrftoken = () => getCookie("csrftoken") || ($("[name=csrfmiddlewaretoken]") || {}).value || "";

  /* ---------- Toast messages ---------- */
  function toast(message, type = "success") {
    let box = $(".messages");
    if (!box) {
      box = document.createElement("div");
      box.className = "messages";
      document.body.appendChild(box);
    }
    const icons = { success: "fa-circle-check", error: "fa-circle-xmark", warning: "fa-triangle-exclamation", info: "fa-circle-info" };
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i><div></div><button class="close" aria-label="${T.close}">&times;</button>`;
    el.querySelector("div").textContent = message;
    box.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }
  window.shopToast = toast;
  document.addEventListener("click", (e) => {
    if (e.target.closest(".toast .close")) e.target.closest(".toast").remove();
  });
  $$(".messages .toast").forEach((t) => setTimeout(() => t.remove(), 5000));

  /* ---------- Dropdown & mobile menu ---------- */
  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-dropdown]");
    $$(".dropdown.open").forEach((d) => { if (!trigger || d !== trigger.parentElement) d.classList.remove("open"); });
    if (trigger) { e.preventDefault(); trigger.parentElement.classList.toggle("open"); }
  });
  /* ---------- Category sub-menus (click the arrow; hover also works on desktop) ---------- */
  document.addEventListener("click", (e) => {
    const toggle = e.target.closest(".sub-toggle");
    $$(".catnav li.open").forEach((li) => {
      if (!toggle || li !== toggle.parentElement) {
        li.classList.remove("open");
        const b = li.querySelector(".sub-toggle");
        if (b) b.setAttribute("aria-expanded", "false");
      }
    });
    if (toggle) {
      e.preventDefault();
      const li = toggle.parentElement;
      const open = li.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") $$(".catnav li.open").forEach((li) => li.classList.remove("open"));
  });
  // if the icon font could not load (offline), show a plain ▾ arrow instead
  window.addEventListener("load", () => {
    const probe = $(".sub-toggle i");
    if (probe && probe.offsetWidth === 0) document.documentElement.classList.add("fa-missing");
  });

  const menuBtn = $(".menu-toggle");
  if (menuBtn) menuBtn.addEventListener("click", () => $(".catnav").classList.toggle("open"));

  /* ---------- Hero slider ---------- */
  const slider = $(".slider");
  if (slider) {
    const slides = $$(".slide", slider);
    const dotsBox = $(".slider-dots", slider);
    let idx = 0, timer;
    slides.forEach((_, i) => {
      const b = document.createElement("button");
      b.setAttribute("aria-label", "Slide " + (i + 1));
      b.addEventListener("click", () => go(i));
      dotsBox && dotsBox.appendChild(b);
    });
    function go(i) {
      if (!slides.length) return;
      idx = (i + slides.length) % slides.length;
      slides.forEach((s, j) => s.classList.toggle("active", j === idx));
      dotsBox && $$("button", dotsBox).forEach((d, j) => d.classList.toggle("active", j === idx));
      clearInterval(timer);
      timer = setInterval(() => go(idx + 1), 5000);
    }
    $(".slider-arrow.prev", slider) && $(".slider-arrow.prev", slider).addEventListener("click", () => go(idx - 1));
    $(".slider-arrow.next", slider) && $(".slider-arrow.next", slider).addEventListener("click", () => go(idx + 1));
    go(0);
  }

  /* ---------- Live search suggestions ---------- */
  const searchInput = $("#search-input");
  const suggestBox = $("#search-suggest");
  if (searchInput && suggestBox) {
    let t;
    searchInput.addEventListener("input", () => {
      clearTimeout(t);
      const q = searchInput.value.trim();
      if (q.length < 2) { suggestBox.classList.add("hidden"); return; }
      t = setTimeout(async () => {
        try {
          const res = await fetch(searchInput.dataset.url + "?q=" + encodeURIComponent(q));
          const data = await res.json();
          suggestBox.innerHTML = "";
          if (!data.results.length) { suggestBox.classList.add("hidden"); return; }
          data.results.forEach((r) => {
            const a = document.createElement("a");
            a.href = r.url;
            a.innerHTML = `<img alt=""><span class="s-name"></span><span class="s-price"></span>`;
            a.querySelector("img").src = r.image;
            a.querySelector(".s-name").textContent = r.name;
            a.querySelector(".s-price").textContent = localDigits("৳" + r.price);
            suggestBox.appendChild(a);
          });
          suggestBox.classList.remove("hidden");
        } catch (err) { suggestBox.classList.add("hidden"); }
      }, 250);
    });
    document.addEventListener("click", (e) => { if (!e.target.closest(".search")) suggestBox.classList.add("hidden"); });
  }

  /* ---------- AJAX add to cart ---------- */
  function setCount(selector, n) { $$(selector).forEach((el) => { el.textContent = n; el.classList.toggle("hidden", !n); }); }

  document.addEventListener("submit", async (e) => {
    const form = e.target.closest("form.js-add-cart");
    if (!form) return;
    const submitter = e.submitter;
    if (submitter && submitter.name === "buy_now") return; // normal submit → checkout
    e.preventDefault();
    const btn = submitter || form.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;
    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrftoken() },
        body: new FormData(form),
      });
      const data = await res.json();
      toast(data.message, data.ok ? "success" : "error");
      if (data.ok) setCount(".js-cart-count", data.cart_count);
    } catch (err) {
      form.submit();
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  /* ---------- Wishlist toggle ---------- */
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".js-wish");
    if (!btn) return;
    e.preventDefault();
    try {
      const res = await fetch(btn.dataset.url, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrftoken() },
      });
      const data = await res.json();
      if (data.login_required) { window.location = btn.dataset.login; return; }
      $$('.js-wish[data-url="' + btn.dataset.url + '"]').forEach((b) => {
        b.classList.toggle("active", data.added);
        const icon = b.querySelector("i");
        if (icon) icon.className = (data.added ? "fa-solid" : "fa-regular") + " fa-heart";
      });
      setCount(".js-wish-count", data.wishlist_count);
      toast(data.message, "success");
      if (!data.added && btn.dataset.removeCard) {
        const card = btn.closest(".product-card");
        if (card) card.remove();
      }
    } catch (err) { toast(T.wrong, "error"); }
  });

  /* ---------- Quantity buttons ---------- */
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".qty button");
    if (!b) return;
    e.preventDefault();
    const input = b.parentElement.querySelector("input");
    const max = parseInt(input.max || "9999", 10);
    let v = parseInt(input.value || "1", 10) + (b.dataset.step === "-" ? -1 : 1);
    v = Math.max(parseInt(input.min || "1", 10), Math.min(max, v));
    input.value = v;
    if (input.form && input.form.classList.contains("js-auto-submit")) input.form.submit();
  });
  $$(".js-auto-submit input[name=quantity]").forEach((i) => i.addEventListener("change", () => i.form.submit()));

  /* ---------- Product gallery ---------- */
  const mainImg = $("#main-image");
  if (mainImg) {
    $$(".thumbs img").forEach((th) => th.addEventListener("click", () => {
      mainImg.src = th.dataset.full;
      $$(".thumbs img").forEach((x) => x.classList.toggle("active", x === th));
    }));
    const box = mainImg.parentElement;
    box.addEventListener("mousemove", (e) => {
      const r = box.getBoundingClientRect();
      mainImg.style.transformOrigin = `${((e.clientX - r.left) / r.width) * 100}% ${((e.clientY - r.top) / r.height) * 100}%`;
    });
    box.addEventListener("mouseenter", () => box.classList.add("zoom"));
    box.addEventListener("mouseleave", () => box.classList.remove("zoom"));
  }

  /* variation price update */
  const priceEl = $("#pd-price");
  if (priceEl) {
    const base = parseFloat(priceEl.dataset.base);
    const update = () => {
      let extra = 0;
      $$(".var-options input:checked").forEach((i) => (extra += parseFloat(i.dataset.extra || 0)));
      priceEl.textContent = localDigits("৳" + Math.round(base + extra).toLocaleString("en-US"));
    };
    $$(".var-options input").forEach((i) => i.addEventListener("change", update));
  }

  /* ---------- Tabs ---------- */
  $$(".tabs").forEach((tabs) => {
    $$("button", tabs).forEach((btn) => btn.addEventListener("click", () => {
      $$("button", tabs).forEach((b) => b.classList.toggle("active", b === btn));
      $$(".tab-panel", tabs.parentElement).forEach((p) => p.classList.toggle("active", p.id === btn.dataset.tab));
    }));
  });
  if (location.hash === "#reviews") { const b = $('[data-tab="reviews"]'); b && b.click(); }

  /* ---------- Flash sale countdown ---------- */
  const cd = $("[data-countdown]");
  if (cd) {
    const end = new Date(cd.dataset.countdown).getTime();
    const pad = (n) => String(n).padStart(2, "0");
    const tick = () => {
      let s = Math.max(0, Math.floor((end - Date.now()) / 1000));
      const h = Math.floor(s / 3600); s -= h * 3600;
      const m = Math.floor(s / 60); s -= m * 60;
      cd.innerHTML = `<span>${T.endsIn}</span><b>${localDigits(pad(h))}</b>:<b>${localDigits(pad(m))}</b>:<b>${localDigits(pad(s))}</b>`;
    };
    tick(); setInterval(tick, 1000);
  }

  /* ---------- Filter sidebar (mobile) ---------- */
  $$("[data-toggle-filters]").forEach((b) => b.addEventListener("click", () => $(".filters").classList.toggle("open")));
  $$(".js-filter-auto").forEach((el) => el.addEventListener("change", () => el.form.submit()));

  /* ---------- Checkout ---------- */
  const checkout = $("#checkout-form");
  if (checkout) {
    const fmt = (n) => localDigits("৳" + Math.round(n).toLocaleString("en-US"));
    const subtotal = parseFloat(checkout.dataset.subtotal);
    const discount = parseFloat(checkout.dataset.discount);
    const shipIn = parseFloat(checkout.dataset.shipInside);
    const shipOut = parseFloat(checkout.dataset.shipOutside);
    const refresh = () => {
      const area = (checkout.querySelector("[name=delivery_area]:checked") || {}).value || "inside";
      const ship = area === "inside" ? shipIn : shipOut;
      $("#sum-shipping").textContent = ship ? fmt(ship) : T.free;
      $("#sum-total").textContent = fmt(subtotal - discount + ship);
      const method = (checkout.querySelector("[name=payment_method]:checked") || {}).value || "cod";
      $$(".pay-info").forEach((p) => p.classList.toggle("hidden", p.dataset.method !== method));
      $$(".mobile-pay-fields").forEach((p) => p.classList.toggle("hidden", method === "cod"));
      const totalTxt = $$(".js-pay-amount");
      totalTxt.forEach((t) => (t.textContent = fmt(subtotal - discount + ship)));
    };
    checkout.addEventListener("change", refresh);
    refresh();

    $$(".addr-card").forEach((card) => card.addEventListener("click", (e) => {
      e.preventDefault();
      const d = card.dataset;
      ["full_name", "phone", "division", "city", "area", "address_line"].forEach((f) => {
        const el = checkout.querySelector(`[name=${f}]`);
        if (el) el.value = d[f.replace("_", "")] || d[f] || "";
      });
      const area = (d.city || "").trim().toLowerCase() === "dhaka" ? "inside" : "outside";
      const radio = checkout.querySelector(`[name=delivery_area][value=${area}]`);
      if (radio) radio.checked = true;
      $$(".addr-card").forEach((c) => c.classList.toggle("active", c === card));
      refresh();
    }));
  }

  /* ---------- Confirm buttons ---------- */
  document.addEventListener("submit", (e) => {
    const f = e.target.closest("form[data-confirm]");
    if (f && !confirm(f.dataset.confirm)) e.preventDefault();
  });

  /* ---------- Back to top ---------- */
  const top = $(".back-top");
  if (top) {
    window.addEventListener("scroll", () => top.classList.toggle("show", window.scrollY > 600));
    top.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  }
})();

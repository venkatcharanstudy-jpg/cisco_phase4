(() => {
  "use strict";

  // Credentials live only in memory for this page session; they are never written to storage.
  const state = { auth: null, user: null, menu: [], cart: new Map(), sessionId: null };

  const $ = (id) => document.getElementById(id);

  function toast(message) {
    const el = $("toast");
    el.textContent = message;
    el.classList.remove("hidden");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.add("hidden"), 3500);
  }

  async function api(method, path, { body, form, headers = {} } = {}) {
    const opts = { method, headers: { ...headers } };
    if (state.auth) opts.headers.Authorization = state.auth;
    if (form) {
      opts.body = form;
    } else if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(path, opts);
    let data = null;
    try { data = await resp.json(); } catch { data = null; }
    if (!resp.ok) {
      const err = new Error((data && data.message) || `Request failed (${resp.status})`);
      err.status = resp.status;
      err.code = data && data.code;
      throw err;
    }
    return data;
  }

  function money(value) {
    return Number(value).toFixed(2);
  }

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  // ----- Auth -----
  async function login(username, password) {
    state.auth = "Basic " + btoa(`${username}:${password}`);
    try {
      state.user = await api("GET", "/api/auth/me");
    } catch (err) {
      state.auth = null;
      throw err;
    }
    $("loginView").classList.add("hidden");
    $("appView").classList.remove("hidden");
    $("who").classList.remove("hidden");
    $("whoName").textContent = `${state.user.username} (${state.user.role})`;
    $("adminView").classList.toggle("hidden", state.user.role !== "ADMIN");
    await Promise.all([loadMenu(), loadOrders()]);
    if (state.user.role === "ADMIN") await loadDocuments();
  }

  function logout() {
    state.auth = null;
    state.user = null;
    state.cart.clear();
    state.sessionId = null;
    $("appView").classList.add("hidden");
    $("who").classList.add("hidden");
    $("loginView").classList.remove("hidden");
    $("loginPass").value = "";
    $("chatLog").replaceChildren();
    $("orders").replaceChildren();
  }

  // ----- Menu and cart -----
  async function loadMenu() {
    state.menu = await api("GET", "/api/menu");
    renderMenu();
    renderCart();
  }

  function renderMenu() {
    const container = $("menu");
    container.replaceChildren();
    for (const item of state.menu) {
      const card = el("div", null, "dish");
      card.append(el("strong", item.title));
      card.append(el("div", `${item.category} · ${money(item.price)}`, "meta"));
      card.append(el("span", item.vegetarian ? "Veg" : "Non-veg", item.vegetarian ? "badge" : "badge nonveg"));
      card.append(el("div", `Available today: ${item.capacity}`, "meta"));
      const addBtn = el("button", "Add to cart");
      addBtn.disabled = item.capacity <= 0;
      addBtn.addEventListener("click", () => addToCart(item));
      card.append(addBtn);
      container.append(card);
    }
  }

  function addToCart(item) {
    const current = state.cart.get(item.id);
    const qty = current ? current.quantity + 1 : 1;
    if (qty > item.capacity) {
      toast(`Only ${item.capacity} of ${item.title} available today`);
      return;
    }
    state.cart.set(item.id, { item, quantity: qty });
    renderCart();
  }

  function renderCart() {
    const list = $("cart");
    list.replaceChildren();
    let total = 0;
    for (const { item, quantity } of state.cart.values()) {
      total += Number(item.price) * quantity;
      const li = el("li");
      li.append(el("span", `${quantity} × ${item.title}`));
      li.append(el("span", money(Number(item.price) * quantity)));
      list.append(li);
    }
    if (state.cart.size === 0) list.append(el("li", "Your cart is empty.", "muted"));
    $("cartTotal").textContent = money(total);
    $("placeOrderBtn").disabled = state.cart.size === 0;
  }

  async function placeOrder() {
    if (state.cart.size === 0) return;
    const items = [...state.cart.values()].map(({ item, quantity }) => ({ item_id: item.id, quantity }));
    $("placeOrderBtn").disabled = true;
    try {
      const order = await api("POST", "/api/orders", {
        body: { items },
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
      state.cart.clear();
      renderCart();
      $("cartMessage").textContent = `Order #${order.id} placed. Total ${money(order.total)}.`;
      await Promise.all([loadMenu(), loadOrders()]);
    } catch (err) {
      toast(err.message);
    } finally {
      $("placeOrderBtn").disabled = state.cart.size === 0;
    }
  }

  // ----- Orders -----
  async function loadOrders() {
    const orders = await api("GET", "/api/orders");
    const container = $("orders");
    container.replaceChildren();
    if (orders.length === 0) {
      container.append(el("p", "No orders yet.", "muted"));
      return;
    }
    for (const order of orders) {
      const box = el("div", null, "order");
      const head = el("div", null, "order-head");
      head.append(el("strong", `Order #${order.id}`));
      head.append(el("span", order.status, "status"));
      box.append(head);
      const names = new Map((state.menu || []).map((m) => [m.id, m.name]));
      box.append(el("div", order.lines.map((l) => `${l.quantity} × ${names.get(l.item_id) || `item ${l.item_id}`}`).join(", "), "meta"));
      box.append(el("div", `Total: ${money(order.total)}`));
      if (order.status === "CONFIRMED" && state.user.role === "CUSTOMER") {
        const cancelBtn = el("button", "Cancel order", "secondary");
        cancelBtn.addEventListener("click", () => cancelOrder(order.id));
        box.append(cancelBtn);
      }
      container.append(box);
    }
  }

  async function cancelOrder(orderId) {
    try {
      await api("POST", `/api/orders/${orderId}/cancel`);
      toast(`Order #${orderId} cancelled`);
      await Promise.all([loadMenu(), loadOrders()]);
    } catch (err) {
      toast(err.message);
    }
  }

  // ----- Chat -----
  function addMessage(role, text, extra) {
    const log = $("chatLog");
    const bubble = el("div", text, `msg ${role}`);
    if (extra && extra.citations && extra.citations.length) {
      const names = [...new Set(extra.citations.map((c) => c.document))];
      bubble.append(el("div", `Sources: ${names.join(", ")}`, "cites"));
    }
    if (extra && extra.pending) bubble.append(renderPending(extra.pending));
    log.append(bubble);
    log.scrollTop = log.scrollHeight;
  }

  function renderPending(pending) {
    const box = el("div", null, "pending");
    const lines = pending.preview && pending.preview.items
      ? pending.preview.items.map((i) => `${i.quantity} × ${i.title}`).join(", ")
      : "";
    const title = pending.action === "create_order" ? "Proposed order" : "Proposed cancellation";
    box.append(el("strong", title));
    if (lines) box.append(el("div", `${lines}${pending.preview.total ? ` · total ${money(pending.preview.total)}` : ""}`));
    if (pending.status === "PENDING") {
      const actions = el("div", null, "actions");
      const confirm = el("button", "Confirm");
      const reject = el("button", "Reject", "secondary");
      confirm.addEventListener("click", () => resolvePending(pending.id, "confirm", box));
      reject.addEventListener("click", () => resolvePending(pending.id, "reject", box));
      actions.append(confirm, reject);
      box.append(actions);
    } else {
      box.append(el("div", `Status: ${pending.status}`, "muted"));
    }
    return box;
  }

  async function resolvePending(actionId, verb, box) {
    const buttons = box.querySelectorAll("button");
    buttons.forEach((b) => (b.disabled = true));
    try {
      const result = await api("POST", `/api/chat/actions/${actionId}/${verb}`);
      box.replaceWith(renderPending(result));
      toast(verb === "confirm" ? "Done" : "Cancelled");
      await Promise.all([loadMenu(), loadOrders()]);
    } catch (err) {
      buttons.forEach((b) => (b.disabled = false));
      toast(err.message);
      if (err.code === "details_changed") await loadOrders();
    }
  }

  async function sendChat(event) {
    event.preventDefault();
    const input = $("chatInput");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    addMessage("user", message);
    try {
      const data = await api("POST", "/api/chat", {
        body: { message, session_id: state.sessionId },
      });
      state.sessionId = data.session_id;
      addMessage("bot", data.reply, { citations: data.citations, pending: data.pending_action });
    } catch (err) {
      addMessage("bot", err.message);
    }
  }

  // ----- Admin -----
  async function loadDocuments() {
    const docs = await api("GET", "/api/admin/documents");
    const container = $("documents");
    container.replaceChildren();
    for (const d of docs) {
      container.append(el("div", `${d.filename} · v${d.version} · ${d.status} · ${d.chunks} chunks`, "muted"));
    }
  }

  async function uploadDocument(event) {
    event.preventDefault();
    const file = $("uploadFile").files[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    try {
      const doc = await api("POST", "/api/admin/documents", { form });
      $("uploadMessage").textContent = `Uploaded ${doc.filename} (version ${doc.version}).`;
      await loadDocuments();
    } catch (err) {
      $("uploadMessage").textContent = err.message;
    }
  }

  async function updateStatus(event) {
    event.preventDefault();
    const orderId = $("statusOrderId").value;
    const status = $("statusValue").value;
    try {
      const order = await api("PATCH", `/api/orders/${orderId}/status`, { body: { status } });
      $("statusMessage").textContent = `Order #${order.id} is now ${order.status}.`;
      await loadOrders();
    } catch (err) {
      $("statusMessage").textContent = err.message;
    }
  }

  // ----- Wiring -----
  $("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    $("loginError").textContent = "";
    try {
      await login($("loginUser").value.trim(), $("loginPass").value);
    } catch (err) {
      $("loginError").textContent = err.status === 401 ? "Invalid username or password." : err.message;
    }
  });
  $("logoutBtn").addEventListener("click", logout);
  $("placeOrderBtn").addEventListener("click", placeOrder);
  $("chatForm").addEventListener("submit", sendChat);
  $("uploadForm").addEventListener("submit", uploadDocument);
  $("statusForm").addEventListener("submit", updateStatus);
  renderCart();
})();

/* Cauvery Peak homepage: deferred hero film, hover clips, live café status.
   Everything here is enhancement; the page is complete without it. */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const conn = navigator.connection || {};
  const slow = conn.saveData || /(^|-)2g|3g/.test(conn.effectiveType || "");

  /* Hero film: no src in the HTML; attach after load + idle, play only while visible. */
  const hero = document.querySelector(".hp-hero__video");
  if (hero && !reduce && !slow) {
    const attach = () => {
      const small = innerWidth < 900;
      if (small) hero.poster = "assets/media/hero-720-poster.webp";
      hero.src = small ? hero.dataset.srcSm : hero.dataset.src;
      hero.addEventListener("playing", () => hero.classList.add("is-playing"), { once: true });
      const io = new IntersectionObserver(([e]) => {
        if (e.isIntersecting && document.visibilityState === "visible") hero.play().catch(() => {});
        else hero.pause();
      });
      io.observe(hero);
      document.addEventListener("visibilitychange", () => (document.hidden ? hero.pause() : hero.play().catch(() => {})));
    };
    const idle = () => (window.requestIdleCallback ? requestIdleCallback(attach, { timeout: 2000 }) : setTimeout(attach, 300));
    document.readyState === "complete" ? idle() : addEventListener("load", idle, { once: true });
  }

  /* Tour stops: a short clip plays on hover/focus with a fine pointer; stills otherwise. */
  if (!reduce && matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.querySelectorAll(".hp-stop").forEach((card) => {
      const v = card.querySelector("video[data-src]");
      if (!v) return;
      const play = () => {
        if (!v.src) v.src = v.dataset.src;
        v.play().then(() => v.classList.add("is-playing")).catch(() => {});
      };
      const stop = () => { v.pause(); v.classList.remove("is-playing"); };
      card.addEventListener("pointerenter", play);
      card.addEventListener("pointerleave", stop);
      card.addEventListener("focusin", play);
      card.addEventListener("focusout", stop);
    });
  }

  /* Live café status in IST. All three close on Tuesdays (client-confirmed, 16 Aug 2026). */
  const now = new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
  const mins = now.getHours() * 60 + now.getMinutes();
  const tuesday = now.getDay() === 2;
  const toMin = (t) => { const [h, m] = t.split(":").map(Number); return h * 60 + m; };
  const fmt = (t) => { let [h, m] = t.split(":").map(Number); const ap = h >= 12 ? "pm" : "am"; h = h % 12 || 12; return m ? `${h}.${String(m).padStart(2, "0")}${ap}` : `${h}${ap}`; };
  let anyOpen = false, earliest = null;
  document.querySelectorAll(".hp-cafe[data-open]").forEach((c) => {
    const [o, cl] = c.dataset.open.split("-");
    const el = c.querySelector(".hp-cafe__state");
    const open = !tuesday && mins >= toMin(o) && mins < toMin(cl);
    if (open) anyOpen = true;
    if (!earliest || toMin(o) < toMin(earliest)) earliest = o;
    if (!el) return;
    el.textContent = tuesday ? "Closed today (Tuesday)" : open ? `Open now · until ${fmt(cl)}` : mins < toMin(o) ? `Opens today at ${fmt(o)}` : "Closed for the day";
    el.classList.toggle("is-open", open);
  });
  const status = document.querySelector("[data-cafe-status]");
  if (status) {
    status.textContent = tuesday ? "Cafés closed today (Tuesday)"
      : anyOpen ? "Cafés open now · until 5pm · closed Tuesdays"
      : `Cafés open daily from ${fmt(earliest || "07:30")} · closed Tuesdays`;
    status.classList.toggle("is-open", anyOpen);
  }
})();

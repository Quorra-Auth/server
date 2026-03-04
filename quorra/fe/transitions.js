function forceReflow(el) {
  // Forces the browser to apply the current styles immediately
  el.getBoundingClientRect();
}

async function waitForTransition(el) {
  const { transitionDuration, transitionDelay } = getComputedStyle(el);

  const toMs = (s) =>
    s.split(",")
      .map(v => v.trim())
      .map(v => v.endsWith("ms") ? parseFloat(v) : parseFloat(v) * 1000);

  const durations = toMs(transitionDuration);
  const delays = toMs(transitionDelay);

  const totalMs = Math.max(
    ...durations.map((d, i) => d + (delays[i] ?? delays[0] ?? 0)),
    0
  );

  if (totalMs === 0) return Promise.resolve();

  return new Promise((resolve) => {
    const done = () => resolve();
    el.addEventListener("transitionend", done, { once: true });
    setTimeout(done, totalMs + 50);
  });
}

async function showStep(nextId) {
  const next = document.getElementById(nextId);
  if (!next) return;

  const current = document.querySelector(".step_div:not(.hidden)");
  if (current === next) return;

  // Exit current
  if (current) {
    current.classList.add("is-exiting");
    await waitForTransition(current);

    current.classList.add("hidden");
    current.classList.remove("is-exiting");
    current.setAttribute("aria-hidden", "true");
  }

  // Enter next (important order)
  next.classList.add("is-entering");   // 1) set start state (opacity 0, translated)
  next.classList.remove("hidden");     // 2) make it participate in layout/paint
  next.setAttribute("aria-hidden", "false");

  forceReflow(next);                  // 3) ensure start state is committed

  requestAnimationFrame(() => {       // 4) transition to final state
    next.classList.remove("is-entering");
  });
}

window.showStep = showStep;

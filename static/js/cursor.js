(() => {
  const cursor = document.getElementById("cursor");
  const ring = document.getElementById("cursorRing");
  if (!cursor || !ring) {
    return;
  }

  if (!window.matchMedia("(pointer: fine)").matches) {
    return;
  }

  let targetX = window.innerWidth / 2;
  let targetY = window.innerHeight / 2;
  let ringX = targetX;
  let ringY = targetY;
  let lastX = targetX;
  let lastY = targetY;
  let isHover = false;
  let isPressed = false;

  const hoverSelector =
    "a, button, input, select, textarea, [role='button'], .bento-card, .suggestion-chip, .item-checkbox, .dish-card, .qchip, .card-cta";

  document.addEventListener("mousemove", (event) => {
    targetX = event.clientX;
    targetY = event.clientY;
    cursor.style.left = `${targetX}px`;
    cursor.style.top = `${targetY}px`;
  });

  document.addEventListener("mouseover", (event) => {
    if (event.target.closest(hoverSelector)) {
      isHover = true;
    }
  });

  document.addEventListener("mouseout", (event) => {
    if (event.target.closest(hoverSelector)) {
      isHover = false;
    }
  });

  document.addEventListener("mousedown", () => {
    isPressed = true;
  });

  document.addEventListener("mouseup", () => {
    isPressed = false;
  });

  const lerp = (start, end, amount) => start + (end - start) * amount;

  const animate = () => {
    ringX = lerp(ringX, targetX, 0.12);
    ringY = lerp(ringY, targetY, 0.12);

    const dx = ringX - lastX;
    const dy = ringY - lastY;
    const speed = Math.min(1.8, Math.hypot(dx, dy) / 12);

    const hoverScale = isHover ? 1.5 : 1;
    const pressScale = isPressed ? 0.88 : 1;
    const ringScale = (1 + speed * 0.18) * hoverScale * pressScale;
    const dotScale = (1 + speed * 0.1) * (isHover ? 1.25 : 1) * (isPressed ? 0.92 : 1);

    ring.style.left = `${ringX}px`;
    ring.style.top = `${ringY}px`;
    ring.style.transform = `translate(-50%, -50%) scale(${ringScale.toFixed(3)})`;
    ring.style.borderColor = isHover
      ? "rgba(212, 168, 67, 0.95)"
      : "rgba(212, 168, 67, 0.55)";

    cursor.style.transform = `translate(-50%, -50%) scale(${dotScale.toFixed(3)})`;

    lastX = ringX;
    lastY = ringY;

    requestAnimationFrame(animate);
  };

  requestAnimationFrame(animate);
})();

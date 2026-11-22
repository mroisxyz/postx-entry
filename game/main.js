/* DODGE - a tiny original browser game. No build step, no dependencies. */
(function () {
  "use strict";

  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("score");
  const W = canvas.width;
  const H = canvas.height;
  const PINK = "#c41b82";

  const keys = Object.create(null);
  const player = { x: W / 2, y: H - 70, w: 46, h: 46, speed: 430 };
  let blocks = [];
  let particles = [];
  let score = 0;
  let elapsed = 0;
  let spawnTimer = 0;
  let state = "ready"; // ready | playing | over
  let last = 0;

  function reset() {
    blocks = [];
    particles = [];
    score = 0;
    elapsed = 0;
    spawnTimer = 0;
    player.x = W / 2;
    state = "playing";
    scoreEl.textContent = "0";
  }

  function spawnBlock() {
    const size = 26 + Math.random() * 30;
    blocks.push({
      x: Math.random() * (W - size),
      y: -size,
      w: size,
      h: size,
      vy: 150 + Math.random() * 120 + elapsed * 3,
      spin: (Math.random() - 0.5) * 2,
      angle: 0,
      hue: Math.random() < 0.5 ? PINK : "#37e0d8",
    });
  }

  function burst(x, y) {
    for (let i = 0; i < 26; i++) {
      const a = (Math.PI * 2 * i) / 26;
      particles.push({
        x, y,
        vx: Math.cos(a) * (60 + Math.random() * 220),
        vy: Math.sin(a) * (60 + Math.random() * 220),
        life: 1,
      });
    }
  }

  function hits(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x &&
           a.y < b.y + b.h && a.y + a.h > b.y;
  }

  function update(dt) {
    if (state === "playing") {
      const dir = (keys.ArrowRight || keys.d || keys.D ? 1 : 0) -
                  (keys.ArrowLeft || keys.a || keys.A ? 1 : 0);
      player.x = Math.max(0, Math.min(W - player.w, player.x + dir * player.speed * dt));

      elapsed += dt;
      score = Math.floor(elapsed * 10);
      scoreEl.textContent = String(score);

      spawnTimer += dt;
      const interval = Math.max(0.28, 0.75 - elapsed * 0.006);
      if (spawnTimer >= interval) { spawnTimer = 0; spawnBlock(); }

      for (const b of blocks) {
        b.y += b.vy * dt;
        b.angle += b.spin * dt;
        if (hits(player, b)) { burst(player.x, player.y); state = "over"; break; }
      }
      blocks = blocks.filter((b) => b.y < H + 60);
    }

    for (const p of particles) {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life -= dt * 1.4;
    }
    particles = particles.filter((p) => p.life > 0);
  }

  function drawGrid() {
    ctx.strokeStyle = "#ffffff0a";
    ctx.lineWidth = 1;
    for (let x = 0; x <= W; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y <= H; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0b0b13";
    ctx.fillRect(0, 0, W, H);
    drawGrid();

    for (const b of blocks) {
      ctx.save();
      ctx.translate(b.x + b.w / 2, b.y + b.h / 2);
      ctx.rotate(b.angle);
      ctx.fillStyle = b.hue;
      ctx.shadowColor = b.hue;
      ctx.shadowBlur = 18;
      ctx.fillRect(-b.w / 2, -b.h / 2, b.w, b.h);
      ctx.restore();
    }

    ctx.save();
    ctx.shadowColor = PINK;
    ctx.shadowBlur = 26;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(player.x, player.y, player.w, player.h);
    ctx.restore();
    ctx.strokeStyle = PINK;
    ctx.lineWidth = 3;
    ctx.strokeRect(player.x, player.y, player.w, player.h);

    ctx.fillStyle = "#ffffff";
    for (const p of particles) {
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.fillRect(p.x, p.y, 5, 5);
    }
    ctx.globalAlpha = 1;

    if (state !== "playing") {
      ctx.fillStyle = "#000000b8";
      ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center";
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 52px Consolas, monospace";
      ctx.fillText(state === "ready" ? "DODGE" : "GAME OVER", W / 2, H / 2 - 10);
      ctx.font = "22px Consolas, monospace";
      ctx.fillStyle = PINK;
      ctx.fillText(
        state === "ready" ? "PRESS SPACE OR CLICK TO START" : "SCORE " + score + "  -  PRESS SPACE TO RETRY",
        W / 2, H / 2 + 38
      );
    }
  }

  function frame(now) {
    const dt = Math.min(0.033, (now - last) / 1000 || 0);
    last = now;
    update(dt);
    draw();
    requestAnimationFrame(frame);
  }

  window.addEventListener("keydown", (e) => {
    keys[e.key] = true;
    if (e.key === " " || e.key === "Spacebar") {
      e.preventDefault();
      if (state !== "playing") reset();
    }
  });
  window.addEventListener("keyup", (e) => { keys[e.key] = false; });
  canvas.addEventListener("click", () => { if (state !== "playing") reset(); });

  requestAnimationFrame(frame);
})();

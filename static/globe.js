/* Local Earth and one synchronized Godfather / specialty / city spotlight. */
(() => {
  'use strict';
  const radians = Math.PI / 180;
  const cities = [
    { code: 'SFO', name: 'San Francisco', specialty: 'Tech', lon: -122.42, lat: 37.77 },
    { code: 'LON', name: 'London', specialty: 'AI', lon: -0.13, lat: 51.51 },
    { code: 'ATH', name: 'Athens', specialty: 'VC', lon: 23.73, lat: 37.98 },
    { code: 'AMS', name: 'Amsterdam', specialty: 'Startups', lon: 4.90, lat: 52.37 },
    { code: 'STO', name: 'Stockholm', specialty: 'Academia', lon: 18.07, lat: 59.33 }
  ];
  const sceneDuration = 4.8;
  function sceneAt(seconds) {
    const elapsed = Math.max(0, seconds);
    const step = Math.floor(elapsed / sceneDuration);
    const index = step % cities.length;
    const phase = elapsed - step * sceneDuration;
    const from = cities[(index + cities.length - 1) % cities.length].lon;
    const to = cities[index].lon;
    const delta = ((to - from + 540) % 360) - 180;
    const travel = Math.min(phase / 1.5, 1);
    const eased = travel * travel * (3 - 2 * travel);
    return { index, center: step === 0 ? to : from + delta * eased, progress: phase / sceneDuration };
  }
  // Simplified coastline outlines, expressed as longitude / latitude.
  const land = [
    [[-168,70],[-145,72],[-128,58],[-110,72],[-85,73],[-62,60],[-55,49],[-70,46],[-81,25],[-97,16],[-105,23],[-118,32],[-125,49],[-143,59],[-166,58]],
    [[-97,22],[-88,21],[-83,10],[-77,8],[-80,4],[-87,15]],
    [[-81,12],[-64,10],[-50,1],[-35,-7],[-43,-23],[-53,-34],[-67,-55],[-75,-47],[-72,-19],[-81,-5]],
    [[-73,60],[-48,59],[-20,74],[-40,83],[-62,80]],
    [[-17,36],[-5,36],[12,37],[33,31],[43,12],[51,11],[43,-12],[35,-23],[20,-35],[11,-20],[8,4],[-5,5],[-17,15]],
    [[-10,36],[-10,44],[-1,49],[-5,58],[8,59],[18,71],[32,70],[45,62],[75,75],[112,73],[140,61],[178,65],[170,51],[145,45],[137,34],[122,25],[108,5],[100,2],[96,20],[80,7],[68,25],[55,25],[44,12],[35,30],[26,40],[14,45],[5,43],[0,36]],
    [[112,-11],[130,-12],[137,-18],[151,-23],[153,-37],[138,-39],[130,-32],[115,-35]],
    [[47,-13],[51,-15],[48,-25],[44,-25]],
    [[130,32],[141,45],[145,43],[138,33]],
    [[-10,50],[-6,59],[0,58],[2,51]],
    [[166,-34],[178,-40],[169,-47],[165,-45]]
  ];
  function inside(lon, lat, polygon) {
    let result = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i], [xj, yj] = polygon[j];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) result = !result;
    }
    return result;
  }
  function project(lon, lat, center) {
    const phi = lat * radians, lambda = (lon - center) * radians, tilt = 18 * radians;
    const depth = Math.cos(phi) * Math.cos(lambda);
    return {
      x: Math.cos(phi) * Math.sin(lambda),
      y: Math.sin(phi) * Math.cos(tilt) - depth * Math.sin(tilt),
      z: Math.sin(phi) * Math.sin(tilt) + depth * Math.cos(tilt)
    };
  }
  function arc(a, b, t) {
    const vector = point => [Math.cos(point.lat * radians) * Math.cos(point.lon * radians), Math.cos(point.lat * radians) * Math.sin(point.lon * radians), Math.sin(point.lat * radians)];
    const av = vector(a), bv = vector(b);
    const angle = Math.acos(Math.max(-1, Math.min(1, av.reduce((sum, value, i) => sum + value * bv[i], 0))));
    if (angle < 0.00001) return { lon: a.lon, lat: a.lat };
    const sin = Math.sin(angle);
    const v = av.map((value, i) => value * Math.sin((1 - t) * angle) / sin + bv[i] * Math.sin(t * angle) / sin);
    return { lon: Math.atan2(v[1], v[0]) / radians, lat: Math.atan2(v[2], Math.hypot(v[0], v[1])) / radians };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { project, arc, cities, sceneAt };
  if (typeof document === 'undefined') return;
  const canvas = document.querySelector('[data-earth]');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const board = canvas.closest('[data-globe-board]');
  const specialty = board.querySelector('[data-godfather-specialty]');
  const location = board.querySelector('[data-godfather-location]');
  const code = board.querySelector('[data-godfather-code]');
  const rotating = board.querySelector('[data-godfather-rotating]');
  const progress = board.querySelector('[data-godfather-progress]');
  let wordAnimation;
  const dots = [];
  for (let lat = -56; lat < 83; lat += 2.4) {
    const step = 2.4 / Math.max(0.25, Math.cos(lat * radians));
    for (let lon = -179; lon < 180; lon += step) {
      if (land.some(polygon => inside(lon, lat, polygon))) dots.push([lon, lat]);
    }
  }
  let elapsed = 0, previous = 0, frame = null, inView = true, selected = -1;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const activeMotion = () => inView && !document.hidden && !reduced.matches && document.documentElement.classList.contains('motion-ready') && !document.documentElement.classList.contains('motion-paused');
  const cx = 450, cy = 450, radius = 342;
  function strokePath(points, center, color, width = 1) {
    ctx.beginPath();
    let pen = false;
    for (const [lon, lat] of points) {
      const p = project(lon, lat, center);
      if (p.z < 0) { pen = false; continue; }
      const x = cx + radius * p.x, y = cy - radius * p.y;
      if (pen) ctx.lineTo(x, y); else ctx.moveTo(x, y);
      pen = true;
    }
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
  }
  function draw() {
    const scene = sceneAt(elapsed);
    const center = scene.center;
    const active = scene.index;
    if (progress) progress.style.transform = `scaleX(${scene.progress})`;
    if (active !== selected) {
      const city = cities[active];
      if (specialty) specialty.textContent = city.specialty;
      if (location) location.textContent = city.name;
      if (code) code.textContent = `${String(active + 1).padStart(2, '0')} / ${city.code}`;
      wordAnimation?.cancel();
      if (selected !== -1 && activeMotion() && rotating?.animate) {
        wordAnimation = rotating.animate([
          { opacity: 0, transform: 'translateY(16px)', filter: 'blur(4px)' },
          { opacity: 1, transform: 'translateY(0)', filter: 'blur(0)' }
        ], { duration: 650, easing: 'cubic-bezier(.2,.75,.25,1)' });
      }
      selected = active;
    }
    ctx.clearRect(0, 0, 900, 900);
    const halo = ctx.createRadialGradient(cx, cy, radius * .95, cx, cy, radius + 46);
    halo.addColorStop(0, '#d4e87925'); halo.addColorStop(1, '#d4e87900');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(cx, cy, radius + 46, 0, Math.PI * 2); ctx.fill();
    const ocean = ctx.createRadialGradient(315, 280, 10, cx, cy, radius);
    ocean.addColorStop(0, '#354536'); ocean.addColorStop(.75, '#1e2d25'); ocean.addColorStop(1, '#101c18');
    ctx.fillStyle = ocean; ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#a4ba7e70'; ctx.lineWidth = 1.5; ctx.stroke();
    for (let lat = -60; lat <= 60; lat += 30) {
      const points = []; for (let lon = -180; lon <= 180; lon += 3) points.push([lon, lat]);
      strokePath(points, center, '#92aa6d24');
    }
    for (let lon = -180; lon < 180; lon += 30) {
      const points = []; for (let lat = -90; lat <= 90; lat += 3) points.push([lon, lat]);
      strokePath(points, center, '#92aa6d24');
    }
    dots.forEach(([lon, lat]) => {
      const p = project(lon, lat, center);
      if (p.z <= 0) return;
      ctx.fillStyle = `rgba(212,232,121,${.24 + p.z * .65})`;
      ctx.beginPath(); ctx.arc(cx + radius * p.x, cy - radius * p.y, 1.3 + p.z * .9, 0, Math.PI * 2); ctx.fill();
    });
    cities.slice(1).forEach((city, i) => {
      const points = [];
      for (let t = 0; t <= 1.001; t += .02) { const p = arc(cities[0], city, Math.min(1, t)); points.push([p.lon, p.lat]); }
      strokePath(points, center, '#f5806375', 1.4);
      const spark = arc(cities[0], city, (elapsed / 4 + i / 4) % 1);
      const p = project(spark.lon, spark.lat, center);
      if (p.z > 0) { ctx.fillStyle = '#f58063'; ctx.beginPath(); ctx.arc(cx + radius * p.x, cy - radius * p.y, 3, 0, Math.PI * 2); ctx.fill(); }
    });
    cities.forEach((city, index) => {
      const p = project(city.lon, city.lat, center);
      if (p.z < .04) return;
      const x = cx + radius * p.x, y = cy - radius * p.y;
      ctx.fillStyle = index === active ? '#f58063' : '#f2efe4';
      ctx.beginPath(); ctx.arc(x, y, index === active ? 6 : 3.5, 0, Math.PI * 2); ctx.fill();
      if (index === active) {
        ctx.strokeStyle = '#f5806380'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(x, y, 11 + 5 * Math.sin(elapsed * 2) ** 2, 0, Math.PI * 2); ctx.stroke();
        ctx.font = 'bold 18px Arial'; ctx.textAlign = 'left'; ctx.fillStyle = '#fcfaf2'; ctx.fillText(city.code, x + 19, y - 12);
      }
    });
  }
  function tick(now) {
    frame = null;
    if (!activeMotion()) { previous = 0; return; }
    if (previous) elapsed += Math.min((now - previous) / 1000, .08);
    previous = now; draw(); frame = window.requestAnimationFrame(tick);
  }
  function sync() {
    if (frame !== null) window.cancelAnimationFrame(frame);
    frame = null; previous = 0;
    if (!activeMotion()) wordAnimation?.cancel();
    draw();
    if (activeMotion()) frame = window.requestAnimationFrame(tick);
  }
  new MutationObserver(sync).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  document.addEventListener('visibilitychange', sync);
  reduced.addEventListener?.('change', sync);
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => { inView = entries[0].isIntersecting; sync(); }, { rootMargin: '100px' }).observe(board);
  window.addEventListener('pagehide', () => { if (frame !== null) window.cancelAnimationFrame(frame); });
  sync();
})();

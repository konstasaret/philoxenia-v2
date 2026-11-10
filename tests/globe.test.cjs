const { test } = require('node:test');
const assert = require('node:assert/strict');
const { project, arc, cities, sceneAt } = require('../static/globe.js');

test('a half-turn puts a visible city behind the globe', () => {
  const city = cities[0];
  assert(project(city.lon, city.lat, city.lon).z > 0);
  assert(project(city.lon, city.lat, city.lon + 180).z < 0);
});
test('projection preserves the unit sphere through a full rotation', () => {
  for (const city of cities) {
    for (let center = -180; center <= 180; center += 15) {
      const p = project(city.lon, city.lat, center);
      assert(Math.abs(p.x ** 2 + p.y ** 2 + p.z ** 2 - 1) < 1e-10);
    }
  }
});
test('connection arcs reach both cities and stay geographically valid', () => {
  for (const city of cities.slice(1)) {
    const start = arc(cities[0], city, 0), end = arc(cities[0], city, 1);
    assert(Math.abs(start.lon - cities[0].lon) < 1e-8);
    assert(Math.abs(end.lon - city.lon) < 1e-8);
    assert(Math.abs(end.lat - city.lat) < 1e-8);
    for (let t = 0; t <= 1; t += .05) {
      const point = arc(cities[0], city, t);
      assert(Number.isFinite(point.lon) && Math.abs(point.lon) <= 180);
      assert(Number.isFinite(point.lat) && Math.abs(point.lat) <= 90);
    }
  }
});

test('every word pair stays tied to the city the globe turns toward', () => {
  const expected = [['Tech', 'San Francisco'], ['AI', 'London'], ['VC', 'Athens'], ['Startups', 'Amsterdam'], ['Academia', 'Stockholm']];
  for (let step = 0; step < 10; step++) {
    const scene = sceneAt(step * 4.8 + 1.6);
    const city = cities[scene.index];
    assert.deepEqual([city.specialty, city.name], expected[step % 5]);
    assert(project(city.lon, city.lat, scene.center).z > .7);
    assert(scene.progress > 0 && scene.progress < 1);
  }
});

test('camera travel stays continuous when the word pair switches, including loop wrap', () => {
  for (let step = 1; step <= 10; step++) {
    const before = sceneAt(step * 4.8 - .00001);
    const after = sceneAt(step * 4.8 + .00001);
    const difference = ((after.center - before.center + 540) % 360) - 180;
    assert(Math.abs(difference) < .001);
    assert.notEqual(before.index, after.index);
  }
});

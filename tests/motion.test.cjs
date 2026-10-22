/* Unit checks for our motion controller. These do not render or control a browser. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/mafia.js'), 'utf8');
function classes() {
  const values = new Set();
  return { add: (...items) => items.forEach(item => values.add(item)), remove: (...items) => items.forEach(item => values.delete(item)), contains: item => values.has(item), toggle: (item, value) => value ? values.add(item) : values.delete(item) };
}
function run({ reduced = false, observerAvailable = true, observerThrows = false } = {}) {
  const root = { classList: classes() };
  const targets = [{ classList: classes() }, { classList: classes() }];
  const events = {};
  const button = { hidden: true, attrs: {}, setAttribute(name, value) { this.attrs[name] = value; }, addEventListener(name, callback) { events[name] = callback; } };
  const preference = { matches: reduced, addEventListener(name, callback) { events.preference = callback; } };
  let observed = [], unobserved = [];
  let reveal;
  const window = { matchMedia: () => preference, addEventListener(name, callback) { events[name] = callback; } };
  if (observerAvailable) window.IntersectionObserver = class {
    constructor(callback) { if (observerThrows) throw new Error('unsupported observer'); reveal = callback; }
    observe(element) { observed.push(element); }
    unobserve(element) { unobserved.push(element); }
  };
  const document = { documentElement: root, querySelector: () => button, querySelectorAll: () => targets, addEventListener(name, callback) { events[name] = callback; } };
  vm.runInNewContext(source, { window, document });
  return { root, targets, button, preference, events, observed, unobserved, reveal };
}
test('motion starts progressively, exposes a working pause and resume control', () => {
  const env = run();
  assert.equal(env.button.hidden, false);
  assert.equal(env.root.classList.contains('motion-ready'), true);
  assert.equal(env.button.textContent, 'Pause motion');
  env.events.click();
  assert.equal(env.root.classList.contains('motion-paused'), true);
  assert.equal(env.button.attrs['aria-pressed'], 'true');
  assert(env.targets.every(target => target.classList.contains('is-visible')));
  env.events.click();
  assert.equal(env.button.textContent, 'Pause motion');
  assert.equal(env.root.classList.contains('motion-paused'), false);
});
test('reduced motion starts with readable content and no active animation', () => {
  const env = run({ reduced: true });
  assert.equal(env.root.classList.contains('motion-paused'), true);
  assert.equal(env.root.classList.contains('reveal-ready'), false);
  assert.equal(env.button.disabled, true);
  assert.equal(env.button.textContent, 'Reduced motion');
  env.events.click();
  assert.equal(env.root.classList.contains('motion-paused'), true);
  assert(env.targets.every(target => target.classList.contains('is-visible')));
});
test('missing observer keeps content visible', () => {
  const env = run({ observerAvailable: false });
  assert.equal(env.root.classList.contains('reveal-ready'), false);
  assert(env.targets.every(target => target.classList.contains('is-visible')));
});
test('observer failure falls back to the complete static page', () => {
  const env = run({ observerThrows: true });
  assert.equal(env.root.classList.contains('motion-ready'), false);
  assert.equal(env.button.hidden, true);
  assert(env.targets.every(target => target.classList.contains('is-visible')));
});
test('intersection reveals an item once, and keyboard focus reveals its parent', () => {
  const env = run();
  assert.equal(env.observed.length, 2);
  env.reveal([{ target: env.targets[0], isIntersecting: true }]);
  assert(env.targets[0].classList.contains('is-visible'));
  assert.equal(env.unobserved.length, 1);
  env.events.focusin({ target: { closest: () => env.targets[1] } });
  assert(env.targets[1].classList.contains('is-visible'));
});
test('preference changes and printing reveal all content safely', () => {
  const env = run();
  env.preference.matches = true;
  env.events.preference({ matches: true });
  assert(env.root.classList.contains('motion-paused'));
  assert(env.targets.every(target => target.classList.contains('is-visible')));
  env.targets.forEach(target => target.classList.remove('is-visible'));
  env.events.beforeprint();
  assert(env.targets.every(target => target.classList.contains('is-visible')));
});

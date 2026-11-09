import test from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
import { fixture } from './fixture.js';
const window = new Window();
for (const name of ['window', 'document', 'HTMLElement', 'customElements', 'CustomEvent', 'Event']) globalThis[name] = window[name];
await import('../src/card.js');
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
async function create(hass = fixture(), config = {}) {
  const card = document.createElement('atomberg-purifier-card');
  card.setConfig(config); card.hass = hass; document.body.append(card); await tick();
  return card;
}
test('renders actual readings and exposes native HA history', async () => {
  const card = await create();
  assert.match(card.shadowRoot.textContent, /836/);
  assert.match(card.shadowRoot.textContent, /91/);
  let detail;
  card.addEventListener('hass-more-info', e => { detail = e.detail; });
  card.shadowRoot.querySelector('[data-info="output_tds"]').click();
  assert.equal(detail.entityId, 'sensor.purifier_output_tds');
  card.shadowRoot.querySelector('[data-tab="insights"]').click();
  assert.match(card.shadowRoot.textContent, /2,100/);
  assert.match(card.shadowRoot.textContent, /full refill cycle is still pending/);
});
test('all control types call the matching HA domain and entity', async () => {
  const hass = fixture(), card = await create(hass);
  card.shadowRoot.querySelector('[data-tab="controls"]').click();
  for (const [key, value] of [['purification_mode', 'RO + UV'], ['fallback_mode', 'TasteTune 50–100 ppm'],
    ['tds_threshold', '230'], ['sleep_start', '02:30'], ['sleep_end', '07:30']]) {
    const input = card.shadowRoot.querySelector(`[data-control="${key}"]`);
    input.value = value; input.dispatchEvent(new Event('change', { bubbles: true })); await tick();
  }
  for (const key of ['display_sleep', 'sleep_schedule']) {
    const input = card.shadowRoot.querySelector(`[data-control="${key}"]`);
    input.checked = !input.checked; input.dispatchEvent(new Event('change', { bubbles: true })); await tick();
  }
  assert.deepEqual(hass.calls.map(x => [x.domain, x.service]), [
    ['select', 'select_option'], ['select', 'select_option'], ['number', 'set_value'],
    ['time', 'set_value'], ['time', 'set_value'], ['switch', 'turn_on'], ['switch', 'turn_off']]);
  assert.deepEqual(hass.calls[2].data, { entity_id: 'number.purifier_tds_threshold', value: 230 });
  assert.equal(hass.calls[3].data.time, '02:30:00');
});
test('a never-pressed refresh button still works', async () => {
  const hass = fixture(), card = await create(hass);
  const button = card.shadowRoot.querySelector('[data-action="refresh"]');
  assert.equal(button.disabled, false); button.click(); await tick();
  assert.deepEqual(hass.calls[0], { domain: 'button', service: 'press', data: { entity_id: 'button.purifier_refresh_readings' } });
});
test('filter life comes from HA entities and opens the correct component history', async () => {
  const card = await create();
  card.shadowRoot.querySelector('[data-tab="filters"]').click();
  assert.equal(card.shadowRoot.querySelectorAll('.filter-item').length, 8);
  assert.match(card.shadowRoot.querySelector('[data-info="ro_membrane_life"]').textContent, /65%/);
  assert.match(card.shadowRoot.textContent, /Estimated remaining life/);
  let detail;
  card.addEventListener('hass-more-info', event => { detail = event.detail; });
  card.shadowRoot.querySelector('[data-info="ro_membrane_life"]').click();
  assert.equal(detail.entityId, 'sensor.purifier_ro_membrane_life');
});
test('unknown filter life is a dash and never a filled healthy bar', async () => {
  const hass = fixture();
  hass.states['sensor.purifier_pre_filter_life'].state = 'unavailable';
  hass.states['sensor.purifier_ro_membrane_life'].state = '101';
  const card = await create(hass);
  card.shadowRoot.querySelector('[data-tab="filters"]').click();
  for (const key of ['pre_filter_life', 'ro_membrane_life']) {
    const item = card.shadowRoot.querySelector(`[data-info="${key}"]`);
    assert.match(item.textContent, /—/);
    assert.equal(item.querySelector('.filter-track').children.length, 0);
  }
  assert.match(card.shadowRoot.querySelector('[data-info="uv_lamp_life"]').textContent, /99%/);
});
test('last read advances when a poll succeeds without changing the water reading', async () => {
  const hass = fixture(), card = await create(hass);
  assert.match(card.shadowRoot.querySelector('.updated').textContent, /12:00:10/);
  hass.states['sensor.purifier_connection'].attributes.last_successful_read = '2026-01-01T12:00:20Z';
  card.hass = hass;
  assert.match(card.shadowRoot.querySelector('.updated').textContent, /Last read 12:00:20/);
  assert.match(card.shadowRoot.textContent, /every 10 seconds/);
  assert.match(card.shadowRoot.querySelector('.reading.output').textContent, /91/);
});
test('service errors are visible and do not fabricate success or update state', async () => {
  const hass = fixture(); hass.callService = async () => { throw new Error('Device did not confirm'); };
  const card = await create(hass); card.shadowRoot.querySelector('[data-tab="controls"]').click();
  const input = card.shadowRoot.querySelector('[data-control="display_sleep"]');
  input.checked = true; input.dispatchEvent(new Event('change', { bubbles: true })); await tick();
  assert.match(card.shadowRoot.querySelector('[role=alert]').textContent, /Device did not confirm/);
  assert.equal(card.shadowRoot.querySelector('[data-control="display_sleep"]').checked, false);
  assert.equal(hass.states['switch.purifier_display_sleep'].state, 'off');
});
test('unavailable, absent analytics and preview never imply healthy zero or send commands', async () => {
  const hass = fixture();
  for (const state of Object.values(hass.states)) state.state = 'unavailable';
  const card = await create(hass);
  assert.match(card.shadowRoot.textContent, /Purifier unavailable/);
  assert.equal(card.shadowRoot.querySelector('[data-action="refresh"]').disabled, true);
  card.shadowRoot.querySelector('[data-tab="insights"]').click();
  assert.match(card.shadowRoot.textContent, /—/);
  const live = await create(); live.preview = true; live.hass = { ...live.hass, locale: { language: 'en-GB' } };
  assert.equal(live.shadowRoot.querySelector('[data-action="refresh"]').disabled, true);
});
test('visual editor saves selection, title and analytics without YAML', async () => {
  const hass = fixture(), editor = document.createElement('atomberg-purifier-card-editor');
  editor.setConfig({}); editor.hass = hass; await tick();
  let config; editor.addEventListener('config-changed', e => { config = e.detail.config; });
  const select = editor.shadowRoot.querySelector('select'); select.value = 'sensor.purifier_input_tds';
  select.dispatchEvent(new Event('change', { bubbles: true }));
  assert.equal(config.entity, 'sensor.purifier_input_tds');
  const title = editor.shadowRoot.querySelector('[data-key="title"]'); title.value = 'Kitchen water';
  title.dispatchEvent(new Event('change', { bubbles: true })); assert.equal(config.title, 'Kitchen water');
});

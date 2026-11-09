import test from 'node:test';
import assert from 'node:assert/strict';
import { bindings, numeric, escapeHtml, validateConfig } from '../src/model.js';
import { fixture } from './fixture.js';

test('discovers a renamed purifier by its integration and device identity', () => {
  const { registry } = fixture();
  registry.find(e => e.unique_id.endsWith('_output_tds')).entity_id = 'sensor.kitchen_water';
  registry.push({ entity_id: 'switch.purifier_display_sleep', platform: 'tuya', device_id: 'fan', unique_id: 'fan_display_sleep' });
  const result = bindings({}, registry);
  assert.equal(result.entities.output_tds, 'sensor.kitchen_water');
  assert.equal(result.entities.display_sleep, 'switch.purifier_display_sleep');
  assert.equal(result.entities.refresh_readings, 'button.purifier_refresh_readings');
});
test('does not choose arbitrarily between purifiers or accept another integration', () => {
  const one = fixture('one', 'one'), two = fixture('two', 'two');
  const registry = [...one.registry, ...two.registry];
  assert.deepEqual(bindings({}, registry).entities, {});
  assert.equal(bindings({ entity: 'sensor.two_input_tds' }, registry).entities.output_tds, 'sensor.two_output_tds');
  assert.deepEqual(bindings({ entity: 'sensor.fan_input_tds' }, registry).entities, {});
  assert.deepEqual(bindings({}, registry.map(e => ({ ...e, platform: 'tuya' }))).entities, {});
});
test('missing, nonfinite and unavailable measurements are not zero', () => {
  for (const value of ['unknown', 'unavailable', '', 'nan', 'Infinity', '-4']) assert.equal(numeric({ state: value }), null);
  assert.equal(numeric(undefined), null);
  assert.equal(numeric({ state: '0' }), 0);
  assert.equal(numeric({ state: '98.7' }), 98.7);
});
test('maps every protocol-key control to its HA entity without relying on its name', () => {
  const { registry } = fixture();
  const mode = registry.find(e => e.unique_id === 'synthetic-device_mode');
  mode.entity_id = 'select.renamed_water_mode';
  const result = bindings({}, registry).entities;
  assert.equal(result.purification_mode, 'select.renamed_water_mode');
  assert.equal(result.display_sleep, 'switch.purifier_display_sleep');
  assert.equal(result.sleep_schedule, 'switch.purifier_sleep_schedule');
  assert.equal(result.sleep_start, 'time.purifier_sleep_start');
  assert.equal(result.sleep_end, 'time.purifier_sleep_end');
  assert.equal(Object.keys(result).filter(key => !key.endsWith('_life')).length, 14);
});
test('untrusted text is escaped and invalid anchors are rejected', () => {
  assert.equal(escapeHtml('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
  assert.throws(() => validateConfig({ entity: 'switch.fan' }));
});

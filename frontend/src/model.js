export const DOMAIN = 'atomberg_purifier_local';
export const FILTERS = [
  ['pre_filter_life', 'Pre-filter'], ['sediment_filter_life', 'Inline sediment'],
  ['pre_carbon_filter_life', 'Pre-carbon'], ['ro_membrane_life', 'RO membrane'],
  ['uf_membrane_life', 'UF membrane'], ['uv_lamp_life', 'UV lamp'],
  ['pump_life', 'Pump'], ['alkaliser_life', 'Alkaliser + taste'],
];
export const FIELDS = {
  input_tds: 'sensor', output_tds: 'sensor', connection: 'sensor',
  lifetime_water: 'sensor', water_saved: 'sensor', runtime: 'sensor',
  purification_mode: 'select', fallback_mode: 'select', tds_threshold: 'number',
  display_sleep: 'switch', sleep_schedule: 'switch', sleep_start: 'time',
  sleep_end: 'time', refresh_readings: 'button',
  ...Object.fromEntries(FILTERS.map(([key]) => [key, 'sensor'])),
};
// Stable integration unique IDs use protocol keys, not translated entity names.
const UNIQUE_KEYS = {
  purification_mode: 'mode', display_sleep: 'idle_sleep', sleep_schedule: 'sleep_mode',
  sleep_start: 'start_utc', sleep_end: 'stop_utc',
};
export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g,
  char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
export const usable = state => !!state && !['unknown', 'unavailable', ''].includes(state.state);
export function numeric(state) {
  if (!usable(state)) return null;
  const number = Number(state.state);
  return Number.isFinite(number) && number >= 0 ? number : null;
}
export function anchors(registry) {
  return registry.filter(e => e.platform === DOMAIN && !e.disabled_by &&
    e.entity_id.startsWith('sensor.') && e.unique_id?.endsWith('_input_tds'));
}
export function bindings(config, registry) {
  const candidates = anchors(registry);
  const anchor = config.entity ? candidates.find(e => e.entity_id === config.entity)
    : candidates.length === 1 ? candidates[0] : undefined;
  if (!anchor) return { entities: {}, reason: candidates.length > 1 && !config.entity
    ? 'Choose a purifier in the card editor.'
    : 'Add the Atomberg Water Purifier Local integration, then choose its purifier in the card editor.' };
  const prefix = anchor.unique_id.slice(0, -'input_tds'.length);
  const entities = {};
  for (const [key, domain] of Object.entries(FIELDS)) {
    const entry = registry.find(e => e.platform === DOMAIN && e.device_id === anchor.device_id &&
      e.unique_id === prefix + (UNIQUE_KEYS[key] || key) && !e.disabled_by && e.entity_id.startsWith(domain + '.'));
    if (entry) entities[key] = entry.entity_id;
  }
  return { entities };
}
export function validateConfig(config) {
  if (config.entity !== undefined && (typeof config.entity !== 'string' ||
      (config.entity && !/^sensor\.[a-z0-9_]+$/.test(config.entity)))) {
    throw new Error('Choose the input TDS sensor belonging to your Atomberg purifier.');
  }
  return { type: 'custom:atomberg-purifier-card', title: 'Intellon', show_analytics: true, ...config };
}

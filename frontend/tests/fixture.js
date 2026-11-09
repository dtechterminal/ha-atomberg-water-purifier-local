import { FIELDS, DOMAIN } from '../src/model.js';
export function fixture(prefix = 'purifier', device = 'synthetic-device') {
  const values = {
    input_tds: '836', output_tds: '91', connection: 'Local network',
    lifetime_water: '1250.5', water_saved: '2100', runtime: '42',
    pre_filter_life: '78', sediment_filter_life: '76', pre_carbon_filter_life: '73',
    ro_membrane_life: '65', uf_membrane_life: '98', uv_lamp_life: '99', pump_life: '95', alkaliser_life: '62',
    purification_mode: 'TasteTune 75–125 ppm', fallback_mode: 'RO + UV',
    tds_threshold: '250', display_sleep: 'off', sleep_schedule: 'on',
    sleep_start: '03:00:00', sleep_end: '08:00:00', refresh_readings: 'unknown',
  };
  const options = ['RO + UV', 'Adaptive', 'TasteTune 50–100 ppm', 'TasteTune 75–125 ppm', 'TasteTune 100–150 ppm', 'Vacay'];
  const registry = [], states = {};
  // Independent contract from the integration's entity constructors.
  const uniqueKeys = { purification_mode: 'mode', display_sleep: 'idle_sleep',
    sleep_schedule: 'sleep_mode', sleep_start: 'start_utc', sleep_end: 'stop_utc' };
  for (const [key, domain] of Object.entries(FIELDS)) {
    const entity_id = `${domain}.${prefix}_${key}`;
    registry.push({ entity_id, platform: DOMAIN, device_id: device, unique_id: `${device}_${uniqueKeys[key] || key}`, disabled_by: null });
    states[entity_id] = { entity_id, state: values[key], last_updated: '2026-01-01T12:00:00Z', attributes: {
      friendly_name: `Water purifier ${key.replaceAll('_', ' ')}`,
      ...(key === 'connection' ? { last_successful_read: '2026-01-01T12:00:10Z', poll_interval_seconds: 10 } : {}),
      ...(key.endsWith('_life') ? { unit_of_measurement: '%', calculation: 'remaining_capacity' } : {}),
      ...(domain === 'select' ? { options: key === 'fallback_mode' ? options.filter(x => !['Adaptive', 'Vacay'].includes(x)) : options } : {}),
      ...(key.includes('tds') ? { unit_of_measurement: 'mg/L', min: 100, max: 300, step: 1 } : {}),
      ...(['lifetime_water', 'water_saved'].includes(key) ? { unit_of_measurement: 'L', mapping_status: 'beta' } : {}),
      ...(key === 'runtime' ? { unit_of_measurement: 'h', mapping_status: 'beta' } : {}),
    } };
  }
  // A button's state is its last press time. 'unknown' before first use is valid.
  return { registry, states, calls: [], locale: { language: 'en' }, config: { time_zone: 'UTC' },
    async callWS() { return registry; },
    async callService(domain, service, data) { this.calls.push({ domain, service, data }); },
  };
}

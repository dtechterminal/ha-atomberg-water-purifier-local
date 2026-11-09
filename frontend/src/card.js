import { DOMAIN, FIELDS, FILTERS, anchors, bindings, escapeHtml as esc, usable, numeric, validateConfig } from './model.js';
import { styles } from './styles.js';
import { drop, refresh, purifier } from './art.js';

const VERSION = '0.2.1';
class AtombergPurifierCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._tab = 'overview';
    this._registry = null;
    this._busy = false;
    this._error = '';
    this._notice = '';
    this._entities = {};
    this.shadowRoot.addEventListener('click', event => this._click(event));
    this.shadowRoot.addEventListener('change', event => this._change(event));
    this.shadowRoot.addEventListener('keydown', event => {
      const tab = event.target.closest('[role=tab]');
      if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const tabs = this._tabs();
      const index = tabs.indexOf(this._tab);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1
        : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      this._tab = tabs[next]; this._render();
      this.shadowRoot.querySelector('[aria-selected=true]')?.focus();
    });
  }
  static getConfigElement() { return document.createElement('atomberg-purifier-card-editor'); }
  static getStubConfig() { return { type: 'custom:atomberg-purifier-card' }; }
  getCardSize() { return this._tab === 'controls' ? 15 : 12; }
  getGridOptions() { return { columns: 12, rows: 'auto', min_columns: 6 }; }
  setConfig(config) {
    this._config = validateConfig(config);
    if (!this._config.show_analytics && this._tab === 'insights') this._tab = 'overview';
    this._fingerprint = null;
    this._render();
  }
  set hass(hass) {
    this._hass = hass;
    if (!this._registry) { this._loadRegistry(); this._render(); return; }
    const resolved = bindings(this._config || {}, this._registry);
    const fingerprint = JSON.stringify([this._config, resolved.entities,
      Object.values(resolved.entities).map(id => hass.states[id]), hass.locale]);
    if (fingerprint !== this._fingerprint) { this._fingerprint = fingerprint; this._render(); }
  }
  get hass() { return this._hass; }
  async _loadRegistry() {
    if (this._loading || !this._hass?.callWS) return;
    this._loading = true;
    try {
      this._registry = await this._hass.callWS({ type: 'config/entity_registry/list' });
      this._registryError = '';
    } catch { this._registryError = 'Could not find your purifier. Try again when Home Assistant is connected.'; }
    finally { this._loading = false; this._render(); }
  }
  _state(key) { return this._hass?.states[this._entities[key]]; }
  _tabs() { return ['overview', 'controls', 'filters', ...(this._config.show_analytics ? ['insights'] : [])]; }
  _available(key) {
    const state = this._state(key);
    // A button is "unknown" until its first press; it is still usable.
    return FIELDS[key] === 'button' ? !!state && state.state !== 'unavailable' : usable(state);
  }
  _disabled(key) { return this._busy || this.preview || !this._available(key) || !this._available('connection'); }
  _value(key, digits = 0) {
    const value = numeric(this._state(key));
    if (value === null) return '—';
    return new Intl.NumberFormat(this._hass?.locale?.language || 'en',
      { maximumFractionDigits: digits }).format(value);
  }
  _unit(key, fallback) { return esc(this._state(key)?.attributes?.unit_of_measurement || fallback); }
  _click(event) {
    const target = event.target.closest('[data-tab],[data-action],[data-info]');
    if (!target || target.disabled) return;
    if (target.dataset.tab) { this._tab = target.dataset.tab; this._error = ''; this._notice = ''; this._render(); }
    else if (target.dataset.action === 'retry') { this._registry = null; this._loadRegistry(); }
    else if (target.dataset.action === 'refresh') this._command('refresh_readings', 'press');
    else if (target.dataset.info && this._entities[target.dataset.info] && !this.preview) {
      this.dispatchEvent(new CustomEvent('hass-more-info', { bubbles: true, composed: true,
        detail: { entityId: this._entities[target.dataset.info] } }));
    }
  }
  _change(event) {
    const input = event.target;
    const key = input.dataset.control;
    if (!key || this._disabled(key)) return;
    if (FIELDS[key] === 'select') {
      if (!this._state(key).attributes.options?.includes(input.value)) return;
      this._command(key, 'select_option', { option: input.value });
    } else if (FIELDS[key] === 'switch') {
      this._command(key, input.checked ? 'turn_on' : 'turn_off');
    } else if (FIELDS[key] === 'number') {
      const value = Number(input.value);
      if (!input.value || !Number.isFinite(value) || !input.checkValidity()) {
        this._error = 'Enter a TDS threshold between 100 and 300 mg/L.'; this._render(); return;
      }
      this._command(key, 'set_value', { value });
    } else if (FIELDS[key] === 'time') {
      if (!/^\d{2}:\d{2}$/.test(input.value) || !input.checkValidity()) return;
      this._command(key, 'set_value', { time: input.value + ':00' });
    }
  }
  async _command(key, service, data = {}) {
    if (this._disabled(key)) return;
    this._busy = true; this._error = ''; this._notice = ''; this._render();
    try {
      await this._hass.callService(FIELDS[key], service, { entity_id: this._entities[key], ...data });
      this._notice = key === 'refresh_readings' ? 'Readings refreshed.' : 'Setting saved.';
    } catch (error) {
      this._error = error?.message || 'The change could not be confirmed. Check the local connection and try again.';
    } finally { this._busy = false; this._render(); }
  }
  _select(key, title, hint = '') {
    const state = this._state(key);
    return `<label class="field"><span>${title}</span><select aria-label="${title}" data-control="${key}" ${this._disabled(key) ? 'disabled' : ''}>
      ${!usable(state) ? '<option>Unavailable</option>' : (state.attributes.options || []).map(option =>
        `<option value="${esc(option)}" ${state.state === option ? 'selected' : ''}>${esc(option)}</option>`).join('')}
      </select>${hint ? `<small>${hint}</small>` : ''}</label>`;
  }
  _toggle(key, title, hint) {
    return `<label class="toggle-row"><span class="toggle-label">${title}<small>${hint}</small></span>
      <input class="toggle" type="checkbox" role="switch" aria-label="${title}" data-control="${key}"
       ${this._state(key)?.state === 'on' ? 'checked' : ''} ${this._disabled(key) ? 'disabled' : ''}></label>`;
  }
  _overview() {
    const output = this._value('output_tds');
    const illustration = purifier.replace('>—</text>', `>${esc(output)}</text>`);
    return `<div class="hero"><span class="hero-caption">DESIGNED AROUND YOUR WATER</span>${illustration}<span class="hero-code">W2 / INTELLON</span></div>
      <div class="quality">${['input_tds', 'output_tds'].map((key, i) => `<button class="reading ${i ? 'output' : ''}" data-info="${key}" aria-label="${i ? 'Output' : 'Input'} TDS history">
        <div class="label">${i ? 'Purified water' : 'Incoming water'}</div><div class="reading-number">${esc(this._value(key))}<span class="unit">${this._unit(key, 'mg/L')}</span></div><div class="label">${i ? 'Output' : 'Input'} TDS ↗</div></button>`).join('')}</div>
      <button class="mode-row" data-tab="controls" aria-label="Change purification mode"><span class="mode-symbol">✳</span><span class="mode-text"><span class="label">Purification mode</span><div class="mode-name">${esc(this._available('purification_mode') ? this._state('purification_mode').state : 'Unavailable')}</div></span><span class="chevron">›</span></button>
      <button class="filter-link" data-tab="filters"><span>Check filter life</span><span>8 components <span class="chevron">›</span></span></button>`;
  }
  _filters() {
    const available = FILTERS.some(([key]) => this._state(key));
    return `<div class="intro"><div><h3>Care, at a glance.</h3><p>Estimated remaining life</p></div><span class="beta">Local</span></div>
      ${!available ? '<div class="health-note">Update Atomberg Water Purifier Local to 0.3.0 or later, restart Home Assistant, then reload this page to see filter life.</div>' : ''}
      <div class="filter-grid">${FILTERS.map(([key, title], index) => {
        const number = numeric(this._state(key));
        const life = number !== null && number <= 100 ? number : null;
        return `<button class="filter-item ${life !== null && life <= 20 ? 'low' : ''}" data-info="${key}" aria-label="${title}: ${life === null ? 'unavailable' : `${life}% estimated life remaining`}">
          <span class="filter-index">${String(index + 1).padStart(2, '0')}</span><span class="filter-name">${title}</span>
          <span class="filter-value">${life === null ? '—' : esc(life)}${life === null ? '' : '<small>%</small>'}</span>
          <span class="filter-track" aria-hidden="true">${life === null ? '' : `<span style="width:${life}%"></span>`}</span></button>`;
      }).join('')}</div>
      <details><summary>How filter life is estimated</summary><p>Calculated from your purifier’s water and runtime counters using Atomberg’s capacity formulas. These readings assume the original filters, UV lamp and pump.</p><p>Past replacements and the app’s flow-performance adjustments are not included. If a component has been replaced, its estimate will be inaccurate. A dash means no reading is available.</p></details>`;
  }
  _controls() {
    const scheduleOn = this._state('sleep_schedule')?.state === 'on';
    const threshold = this._state('tds_threshold');
    return `<div class="intro"><div><h3>Make it yours.</h3><p>Your water preferences, controlled locally.</p></div></div>
      <div class="section-label">Purification</div>
      ${this._select('purification_mode', 'Purification mode')}
      ${this._select('fallback_mode', 'Fallback mode', 'Used when the purifier needs an alternative purification mode.')}
      <label class="field"><span>Input TDS threshold <span class="unit">mg/L</span></span><input type="number" aria-label="Input TDS threshold" data-control="tds_threshold" min="${esc(threshold?.attributes.min ?? 100)}" max="${esc(threshold?.attributes.max ?? 300)}" step="${esc(threshold?.attributes.step ?? 1)}" value="${this._available('tds_threshold') ? esc(threshold.state) : ''}" ${this._disabled('tds_threshold') ? 'disabled' : ''}><small>In Adaptive mode, this decides which purification path to use.</small></label>
      <div class="section-label">Display & rest</div>
      ${this._toggle('display_sleep', 'Display sleep', 'Turn off the display while the purifier is idle.')}
      ${this._toggle('sleep_schedule', 'Sleep schedule', 'Pause purification during a daily sleep window.')}
      <div class="time-grid">${[['sleep_start', 'Sleep starts'], ['sleep_end', 'Sleep ends']].map(([key, title]) => `<label class="field"><span>${title}</span><input type="time" aria-label="${title}" data-control="${key}" value="${this._available(key) ? esc(this._state(key).state.slice(0, 5)) : ''}" ${this._disabled(key) || !scheduleOn ? 'disabled' : ''}></label>`).join('')}</div>
      <p class="save-note">${scheduleOn ? 'Times follow your Home Assistant time zone.' : 'Enable Sleep schedule to change its times.'} Changes are confirmed by the purifier.</p>`;
  }
  _insights() {
    return `<div class="intro"><div><h3>Every litre counts.</h3><p>Lifetime readings from your purifier.</p></div><span class="beta">Beta</span></div>
      <div class="saved-water"><div class="label">Estimated water saved</div><div class="big">${esc(this._value('water_saved'))}<span class="unit">${this._unit('water_saved', 'L')}</span></div><div class="water-art">${drop}</div></div>
      <div class="metric-grid"><button class="metric" data-info="lifetime_water"><div class="label">Lifetime water ↗</div><div class="metric-value">${esc(this._value('lifetime_water', 1))}<span class="unit">${this._unit('lifetime_water', 'L')}</span></div></button>
      <button class="metric" data-info="runtime"><div class="label">Purifier runtime ↗</div><div class="metric-value">${esc(this._value('runtime', 1))}<span class="unit">${this._unit('runtime', 'h')}</span></div></button></div>
      <details><summary>About these readings</summary><p>These beta readings match the W2 app. Comparison through a full refill cycle is still pending. They are lifetime device counters, not a measure of what you just dispensed.</p><p>Water saved is Atomberg’s estimate against a 25% recovery purifier: RO litres × 1.5 + UF litres × 3. Missing readings are shown as a dash. Update the local integration to version 0.2.0 or later to get these sensors.</p></details>
      <button class="filter-link" data-tab="filters"><span>View filter life</span><span class="chevron">›</span></button>`;
  }
  _render() {
    if (!this._config || !this._hass) return;
    const active = this.shadowRoot.activeElement;
    const focus = active?.dataset.control;
    const draft = focus ? { value: active.value, start: active.selectionStart, end: active.selectionEnd } : null;
    const resolution = bindings(this._config, this._registry || []);
    this._entities = resolution.entities;
    const connected = this._available('connection') && this._available('output_tds');
    const lastRead = this._state('connection')?.attributes?.last_successful_read;
    const updated = lastRead || this._state('output_tds')?.last_updated;
    const date = updated ? new Date(updated) : null;
    const time = date && Number.isFinite(date.getTime()) ? new Intl.DateTimeFormat(this._hass.locale?.language || 'en', { hour: 'numeric', minute: '2-digit', second: '2-digit', timeZone: this._hass.config?.time_zone }).format(date) : '—';
    let body;
    if (!this._registry) body = `<div class="waiting">${esc(this._registryError || 'Finding your purifier…')}${this._registryError ? '<br><button class="retry" data-action="retry">Try again</button>' : ''}</div>`;
    else if (resolution.reason) body = `<div class="content"><div class="empty"><strong>A home for your purifier.</strong>${esc(resolution.reason)}<br><button class="retry" data-action="retry">Find purifier</button></div></div>`;
    else body = `${!connected ? '<div class="offline-banner">Purifier unavailable. Check its power, Wi-Fi and local connection to Home Assistant.</div>' : ''}
      <nav class="tabs" role="tablist" aria-label="Purifier pages">${this._tabs().map(tab => `<button class="tab" id="tab-${tab}" role="tab" aria-selected="${tab === this._tab}" aria-controls="page" tabindex="${tab === this._tab ? 0 : -1}" data-tab="${tab}">${tab[0].toUpperCase() + tab.slice(1)}</button>`).join('')}</nav>
      <section class="content" id="page" role="tabpanel" aria-labelledby="tab-${this._tab}">${this._tab === 'controls' ? this._controls() : this._tab === 'filters' ? this._filters() : this._tab === 'insights' ? this._insights() : this._overview()}
      <div class="footer"><span class="updated">${connected ? (lastRead ? 'Auto-refresh · every 10 seconds' : 'Local connection') : 'Connection unavailable'}<br>${lastRead ? 'Last read' : 'Last change'} ${esc(time)}</span><button class="refresh ${this._busy ? 'spinning' : ''}" data-action="refresh" aria-label="Refresh readings" ${this._disabled('refresh_readings') ? 'disabled' : ''}>${refresh}<span>${this._busy ? 'Working…' : 'Refresh'}</span></button></div></section>`;
    this.shadowRoot.innerHTML = `<style>${styles}</style><ha-card><header><span class="mark">${drop}</span><div class="identity"><div class="eyebrow">ATOMBERG · WATER PURIFIER</div><h2>${esc(this._config.title)}</h2></div><span class="connection ${connected ? '' : 'offline'}"><span class="dot"></span>${connected ? 'Local' : 'Offline'}</span></header>${this._error ? `<div class="message" role="alert">${esc(this._error)}</div>` : ''}${this._notice ? `<div class="message notice" role="status">${esc(this._notice)}</div>` : ''}${body}</ha-card>`;
    if (focus && !this._busy) {
      const input = this.shadowRoot.querySelector(`[data-control="${focus}"]`);
      if (input && !input.disabled) {
        input.focus();
        // Preserve an uncommitted input if an unrelated HA update arrives.
        if (draft && input.tagName === 'INPUT' && !['checkbox'].includes(input.type)) {
          input.value = draft.value;
          if (['text', 'search', 'tel', 'url', 'password'].includes(input.type)) input.setSelectionRange(draft.start, draft.end);
        }
      }
    }
  }
}

class AtombergPurifierEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._registry = [];
    this.shadowRoot.addEventListener('change', event => {
      const key = event.target.dataset.key;
      if (!key) return;
      this._config = { ...this._config, [key]: event.target.type === 'checkbox' ? event.target.checked : event.target.value };
      if (key === 'entity' && !this._config.entity) delete this._config.entity;
      this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this._config }, bubbles: true, composed: true }));
    });
  }
  setConfig(config) { this._config = validateConfig(config); this._render(); }
  set hass(hass) {
    this._hass = hass;
    if (!this._loaded && !this._loading && hass.callWS) {
      this._loading = true;
      hass.callWS({ type: 'config/entity_registry/list' }).then(entries => { this._registry = entries; this._loaded = true; this._render(); })
        .catch(() => { this._error = true; this._render(); }).finally(() => { this._loading = false; });
    }
    this._render();
  }
  _render() {
    if (!this._config || !this._hass || this.shadowRoot.activeElement) return;
    const options = anchors(this._registry);
    this.shadowRoot.innerHTML = `<style>:host{display:block;padding:8px 0}label{display:block;margin:16px 0;font-size:14px}select,input[type=text]{display:block;width:100%;box-sizing:border-box;margin-top:8px;padding:12px;border-radius:8px;border:1px solid var(--divider-color,#888);background:var(--card-background-color,#fff);color:var(--primary-text-color,#222);font:inherit}p{font-size:13px;color:var(--secondary-text-color,#666);line-height:1.6}</style>
      <label>Purifier<select data-key="entity" aria-label="Purifier"><option value="">Find automatically (one purifier)</option>${options.map(e => `<option value="${esc(e.entity_id)}" ${this._config.entity === e.entity_id ? 'selected' : ''}>${esc(this._hass.states[e.entity_id]?.attributes.friendly_name || e.entity_id)}</option>`).join('')}</select></label>
      <label>Card title<input type="text" data-key="title" aria-label="Card title" value="${esc(this._config.title)}"></label>
      <label><input type="checkbox" data-key="show_analytics" ${this._config.show_analytics ? 'checked' : ''}> Show Insights (beta analytics)</label>
      <p>${this._error ? 'Could not load the device list. Reopen the editor when Home Assistant is connected.' : 'Install Atomberg Water Purifier Local first. With one purifier, the card finds all its entities automatically—even if you rename them.'}</p>`;
  }
}
if (!customElements.get('atomberg-purifier-card')) customElements.define('atomberg-purifier-card', AtombergPurifierCard);
if (!customElements.get('atomberg-purifier-card-editor')) customElements.define('atomberg-purifier-card-editor', AtombergPurifierEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === 'atomberg-purifier-card')) window.customCards.push({
  type: 'atomberg-purifier-card', name: 'Atomberg Purifier', preview: true,
  description: 'Intellon readings, local controls and lifetime analytics.',
});
console.info(`ATOMBERG PURIFIER CARD ${VERSION}`);

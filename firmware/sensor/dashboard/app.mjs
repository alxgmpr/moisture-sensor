import {SMP_SERVICE, SERVICE, CONFIG, STATUS, DEFAULTS, encode, decode, decodeStatus, commands, activity, moisture} from './protocol.mjs';
const $ = id => document.getElementById(id), form = $('settings');
let device, configChar, statusChar, status, saved, demo = false, busy = false, polling = false, receivedAt = 0;
const connected = () => demo || !!device?.gatt?.connected;
const message = (text, error = false) => { $('message').textContent = text; $('message').classList.toggle('error', error); };
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function values() {
  const c = {};
  for (const k of Object.keys(DEFAULTS)) c[k] = k === 'name' ? form.elements[k].value : k === 'calibrated' ? form.elements[k].checked : k === 'window' ? Number(form.elements.windowSeconds.value) * 1000 : Number(form.elements[k].value);
  return c;
}
function fill(c) {
  for (const [k, v] of Object.entries(c)) {
    if (k === 'calibrated') form.elements[k].checked = v;
    else if (k === 'window') form.elements.windowSeconds.value = v / 1000;
    else if (form.elements[k]) form.elements[k].value = v;
  }
  render();
}
function statusAge() { return (status?.age ?? 0) + Math.floor((Date.now() - receivedAt) / 1000); }
function render() {
  const c = values(); let valid = true;
  try { encode(c); } catch { valid = false; }
  const active = connected();
  $('connect').disabled = busy || (active && !demo) || !navigator.bluetooth || !window.isSecureContext;
  $('disconnect').hidden = !active;
  $('disconnect').disabled = busy;
  $('demo').hidden = active;
  $('save').disabled = !active || busy || !valid || status?.storageFault;
  $('reload').disabled = !active || busy;
  $('measure').disabled = !active || busy || status?.maintenance;
  $('connection-dot').classList.toggle('connected', active);
  for (const button of document.querySelectorAll('[data-capture]')) button.disabled = !active || busy || !status?.valid || statusAge() > 30;
  for (const input of form.querySelectorAll('input')) input.disabled = busy && !polling;
  for (const b of document.querySelectorAll('[data-preset]')) b.disabled = busy;
  $('save').textContent = demo ? 'Save in demo' : 'Save to sensor ↗';
  const dirty = !valid || !saved || !encode(c).every((v, i) => v === encode(saved)[i]);
  $('save-state').textContent = demo ? (dirty ? 'Demo · unsaved changes' : 'Demo configuration') : active ? (dirty ? 'Unsaved changes' : status?.stored ? 'Stored on sensor' : 'Device defaults · not yet saved') : 'Offline configuration';
  $('save-detail').textContent = demo ? 'Demo data only. No Bluetooth device is changed.' : active ? 'Name, calibration and radio settings apply on the next wake.' : 'Connect to read your device’s configuration.';
  if (valid) {
    const a = activity(c), fmt = n => Math.round(n).toLocaleString();
    $('events-day').textContent = fmt(a.perDay); $('measurements-day').textContent = fmt(a.measurements);
    $('events-wake').textContent = a.events.toFixed(1); $('awake-duty').textContent = `${a.awake.toFixed(2)}%`;
    $('awake-bar').style.width = `${a.awake}%`;
    const previousDevelopment = 86400 / 360 * 300000 / 130;
    $('comparison').textContent = a.perDay < previousDevelopment ? `About ${(previousDevelopment / a.perDay).toFixed(0)}× fewer advertising events than the old 5-minute-on / 1-minute-off development schedule (125 ms baseline plus random delay).` : 'This schedule exceeds the old development image’s estimated radio event rate.';
  } else {
    for (const id of ['events-day', 'measurements-day', 'events-wake', 'awake-duty']) $(id).textContent = '—';
    $('comparison').textContent = 'Adjust the settings to a valid schedule to see its radio activity.';
  }
  if (status) {
    $('battery').textContent = status.valid ? `${(status.battery / 1000).toFixed(2)} V` : '—';
    $('temperature').textContent = status.valid ? `${status.temperature.toFixed(1)} °C` : '—';
    $('humidity').textContent = status.valid ? `${status.humidity.toFixed(1)}% relative humidity` : 'No valid measurement';
    for (const i of [1, 2]) {
      $(`raw${i}`).textContent = status.valid ? `${status[`raw${i}`]} fF · CAPDAC ${status[`capdac${i}`]}` : 'No valid measurement';
      $(`moisture${i}`).textContent = status.valid && c.calibrated && valid ? `${moisture(status[`raw${i}`], c[`dry${i}`], c[`wet${i}`]).toFixed(1)}%` : '—';
    }
    $('sample-age').textContent = status.valid ? `${demo ? 'Demo · ' : ''}${statusAge()} seconds since sample` : `Measurement error: ${status.sampleError}`;
    const left = Math.max(0, status.remaining - Math.floor((Date.now() - receivedAt) / 1000));
    $('session-status').textContent = active ? `${left} seconds left in this connection${demo ? ' (demo)' : ''}.` : 'Disconnected. Reconnect during a future advertising window.';
  }
}
async function exclusive(action, background = false) {
  if (busy) return;
  busy = true; polling = background; render();
  try { await action(); } catch (error) { message(error.message || String(error), true); }
  finally { busy = false; polling = false; render(); }
}
async function readStatus() {
  if (!demo) status = decodeStatus(await statusChar.readValue());
  receivedAt = Date.now();
  render();
  return status;
}
async function readDevice() {
  const c = demo ? {...saved} : decode(await configChar.readValue());
  await readStatus(); saved = c; fill(c);
  $('device-meta').textContent = `${demo ? 'DEMO · ' : ''}Firmware ${status.version} · ${status.maintenance ? 'Maintenance mode' : 'BTHome v2'} · ${status.stored ? 'Persistent settings' : 'Build defaults'}`;
  if (status.storageFault) message(`Configuration storage error ${status.saveError}. Saving is disabled; existing storage has not been erased.`, true);
}
function disconnected() {
  demo = false; configChar = statusChar = null;
  $('connection').textContent = 'Sensor disconnected';
  message('Disconnected. Your edits remain in the form. Reconnect to check the device’s saved settings.');
  render();
}
$('connect').addEventListener('click', () => exclusive(async () => {
  if (demo) { demo = false; status = null; }
  message('Choose your sensor. If it is asleep, reinsert the battery or wait for its next window.');
  device = await navigator.bluetooth.requestDevice({filters: [{services: [SMP_SERVICE]}], optionalServices: [SERVICE]});
  device.addEventListener('gattserverdisconnected', disconnected);
  try {
    const server = await device.gatt.connect();
    let service;
    try { service = await server.getPrimaryService(SERVICE); }
    catch { throw Error('This sensor does not expose the configuration service. Install firmware 0.2.9 or later through SMP OTA, then reconnect.'); }
    configChar = await service.getCharacteristic(CONFIG); statusChar = await service.getCharacteristic(STATUS);
    await readDevice(); $('connection').textContent = device.name || 'Moisture sensor';
    if (!status.storageFault) message('Connected. Readings are from the last measurement; use Measure now for calibration.');
  } catch (error) { device.gatt.disconnect(); throw error; }
}));
$('disconnect').addEventListener('click', () => { if (demo) disconnected(); else device?.gatt.disconnect(); });
$('reload').addEventListener('click', () => exclusive(async () => { await readDevice(); if (!status.storageFault) message('Configuration reloaded from the sensor.'); }));
form.addEventListener('input', render);
form.addEventListener('submit', event => {
  event.preventDefault();
  exclusive(async () => {
    if (!connected()) throw Error('Connect a sensor before saving.');
    const c = values(), wire = encode(c);
    if (demo) { saved = c; status.stored = true; message('Saved in demo memory only. No device was changed.'); return; }
    const before = (await readStatus()).saves;
    if (status.remaining < 10) throw Error('Connection is about to expire. Reconnect before saving.');
    message('Saving to the sensor and checking persistent storage…');
    try {
      for (const command of commands(wire)) await configChar.writeValueWithResponse(command);
      const deadline = Date.now() + 10000;
      do {
        await sleep(200); await readStatus();
        if (status.saveError) throw Error(`Sensor could not save configuration (error ${status.saveError}).`);
        if (!status.saving && status.saves !== before) {
          const actual = decode(await configChar.readValue());
          if (!encode(actual).every((v, i) => v === wire[i])) throw Error('Saved configuration readback does not match.');
          saved = actual; fill(actual);
          message('Saved and verified on the sensor. Disconnect to let it sleep; settings apply on the next wake.');
          return;
        }
      } while (Date.now() < deadline);
      throw Error('Timed out waiting for durable save confirmation.');
    } catch (error) { throw Error(`${error.message} Save outcome is unconfirmed: reconnect and reload before retrying.`); }
  });
});
$('measure').addEventListener('click', () => exclusive(async () => {
  if (!connected()) throw Error('Connect a sensor first.');
  message('Taking a fresh measurement…');
  if (demo) { status.age = 0; receivedAt = Date.now(); message('Demo sample refreshed. Values are simulated.'); return; }
  await readStatus();
  if (status.remaining < 10) throw Error('Reconnect before starting another measurement; this connection is ending.');
  await configChar.writeValueWithResponse(Uint8Array.of(4));
  const deadline = Date.now() + 10000;
  do {
    await sleep(250); await readStatus();
    if (!status.measuring) {
      if (!status.valid) throw Error(`Measurement failed (${status.sampleError}).`);
      message('Fresh raw readings received. Capture the appropriate dry or wet endpoint, then save.'); return;
    }
  } while (Date.now() < deadline);
  throw Error('Measurement timed out. Reconnect and check the sensor.');
}));
for (const button of document.querySelectorAll('[data-capture]')) button.addEventListener('click', () => {
  if (!status?.valid || statusAge() > 30) { message('Take a fresh measurement before capturing an endpoint.', true); return; }
  const key = button.dataset.capture;
  form.elements[key].value = status[`raw${key.at(-1)}`];
  message(`Captured probe ${key.at(-1)} ${key.startsWith('dry') ? 'dry' : 'wet'} reference. Save to keep it on the sensor.`); render();
});
for (const button of document.querySelectorAll('[data-preset]')) button.addEventListener('click', () => {
  const presets = {balanced: {cycle: 900, lowCycle: 3600, window: 5000, advertising: 500}, quiet: {cycle: 3600, lowCycle: 14400, window: 5000, advertising: 500}, bench: {cycle: 60, lowCycle: 3600, window: 30000, advertising: 1000}};
  fill({...values(), ...presets[button.dataset.preset]}); message('Preset applied to the form. Save to apply it to the device.');
});
$('demo').addEventListener('click', () => {
  demo = true; saved = {...DEFAULTS, name: 'Fern'};
  status = {valid: true, stored: true, saving: false, storageFault: false, maintenance: false,
    battery: 3062, temperature: 24.8, humidity: 43.2, raw1: 3990, raw2: 3850,
    capdac1: 0, capdac2: 0, age: 3, sampleError: 0, saveError: 0, remaining: 300, version: '0.2.9'};
  receivedAt = Date.now(); fill(saved); $('connection').textContent = 'Demo sensor · Fern';
  $('device-meta').textContent = 'DEMO · Simulated readings · No Bluetooth connection';
  message('Demo mode. Explore settings and calibration without changing a physical sensor.');
});
setInterval(() => {
  render();
}, 1000);
setInterval(() => {
  if (connected() && !demo && !busy) exclusive(readStatus, true);
}, 5000);
window.addEventListener('pagehide', () => device?.gatt?.disconnect());
fill(DEFAULTS);
if (!navigator.bluetooth || !window.isSecureContext) message('Bluetooth needs a supported Chrome or Edge browser on localhost or HTTPS. Demo mode is available here.');

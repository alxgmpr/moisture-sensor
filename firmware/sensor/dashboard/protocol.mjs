export const SMP_SERVICE = '8d53dc1d-1db7-4cd3-868b-8a527460aa84';
export const SERVICE = '6d6f6973-7475-7265-8000-000000000001';
export const CONFIG = '6d6f6973-7475-7265-8000-000000000002';
export const STATUS = '6d6f6973-7475-7265-8000-000000000003';
export const DEFAULTS = Object.freeze({name: '', cycle: 900, lowCycle: 3600, window: 5000,
  advertising: 500, session: 300, lowMv: 2500, calibrated: true,
  dry1: 2655, wet1: 5658, dry2: 2618, wet2: 5571});
const numbers = ['cycle', 'lowCycle', 'window', 'advertising', 'session', 'lowMv', 'dry1', 'wet1', 'dry2', 'wet2'];
export function validate(c) {
  if (numbers.some(k => !Number.isSafeInteger(c[k]))) throw Error('All numeric settings must be whole numbers.');
  if (typeof c.name !== 'string' || !/^[\x20-\x7e]{0,11}$/.test(c.name)) throw Error('Name must be at most 11 plain ASCII characters.');
  if (typeof c.calibrated !== 'boolean') throw Error('Calibration switch must be on or off.');
  if (c.cycle < 60 || c.cycle > 86400) throw Error('Measurement interval must be 60–86400 seconds.');
  if (c.lowCycle < c.cycle || c.lowCycle > 604800) throw Error('Low-battery interval must be at least the normal interval and at most 7 days.');
  if (c.window < 5000 || c.window > 300000 || c.window > c.cycle * 500) throw Error('Advertising window must be 5–300 seconds and at most half the measurement interval.');
  if (c.advertising < 100 || c.advertising > 5000 || c.advertising % 5 || c.window < c.advertising * 5) throw Error('Advertising spacing must be 100–5000 ms, in steps of 5, with at least 5 events per window.');
  if (c.session < 30 || c.session > 900) throw Error('Connection limit must be 30–900 seconds.');
  if (c.lowMv < 800 || c.lowMv > 3300) throw Error('Low-battery threshold must be 800–3300 mV (below 2200 requires firmware 0.2.11 or newer).');
  for (const i of [1, 2]) {
    if (c[`dry${i}`] < -15000 || c[`dry${i}`] > 115000 || c[`wet${i}`] < -15000 || c[`wet${i}`] > 115000 || c[`dry${i}`] === c[`wet${i}`]) throw Error(`Probe ${i}: endpoints must differ and be between −15000 and 115000 fF.`);
  }
  return c;
}
export function encode(c) {
  validate(c);
  const bytes = new Uint8Array(64), v = new DataView(bytes.buffer);
  bytes[0] = 1; bytes[1] = Number(c.calibrated); bytes[2] = c.name.length;
  v.setUint32(4, c.cycle, true); v.setUint32(8, c.lowCycle, true); v.setUint32(12, c.window, true);
  v.setUint16(16, c.advertising, true); v.setUint16(18, c.session, true); v.setUint16(20, c.lowMv, true);
  ['dry1', 'wet1', 'dry2', 'wet2'].forEach((k, i) => v.setInt32(24 + i * 4, c[k], true));
  bytes.set(new TextEncoder().encode(c.name), 40);
  return bytes;
}
export function decode(v) {
  if (v.byteLength !== 64 || v.getUint8(0) !== 1) throw Error('Unsupported sensor configuration version.');
  const bytes = new Uint8Array(v.buffer, v.byteOffset, v.byteLength);
  const n = bytes[2];
  if (bytes[1] > 1 || n > 11 || bytes[3] || bytes[22] || bytes[23] || bytes.slice(40 + n).some(Boolean)) throw Error('Invalid configuration response.');
  const c = {name: new TextDecoder().decode(bytes.slice(40, 40 + n)), calibrated: !!bytes[1],
    cycle: v.getUint32(4, true), lowCycle: v.getUint32(8, true), window: v.getUint32(12, true),
    advertising: v.getUint16(16, true), session: v.getUint16(18, true), lowMv: v.getUint16(20, true)};
  ['dry1', 'wet1', 'dry2', 'wet2'].forEach((k, i) => c[k] = v.getInt32(24 + i * 4, true));
  return validate(c);
}
export function decodeStatus(v) {
  if (v.byteLength !== 48 || v.getUint8(0) !== 1) throw Error('Unsupported sensor status version.');
  const flags = v.getUint8(1);
  return {valid: !!(flags & 1), stored: !!(flags & 2), saving: !!(flags & 4), storageFault: !!(flags & 8),
    maintenance: !!(flags & 16), measuring: !!(flags & 32), battery: v.getUint16(2, true),
    temperature: v.getInt16(4, true) / 100, humidity: v.getUint16(6, true) / 100,
    raw1: v.getInt32(8, true), raw2: v.getInt32(12, true), age: v.getUint32(16, true),
    sampleError: v.getInt32(20, true), saveError: v.getInt32(24, true), saves: v.getUint32(28, true),
    remaining: v.getUint16(32, true), version: `${v.getUint8(34)}.${v.getUint8(35)}.${v.getUint8(36) | v.getUint8(39) << 8}`,
    capdac1: v.getUint8(37), capdac2: v.getUint8(38)};
}
export function crc32(data) {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (~crc) >>> 0;
}
export function commands(bytes) {
  const out = [Uint8Array.of(1)];
  for (let i = 0; i < bytes.length; i += 18) out.push(Uint8Array.of(2, i, ...bytes.slice(i, i + 18)));
  const commit = new Uint8Array(5); commit[0] = 3;
  new DataView(commit.buffer).setUint32(1, crc32(bytes), true);
  return [...out, commit];
}
export function activity(c) {
  const events = c.window / (c.advertising + 5); // Mean BLE random delay, not a packet count.
  return {events, perDay: events * 86400 / c.cycle, awake: 100 * c.window / (c.cycle * 1000), measurements: 86400 / c.cycle};
}
export function moisture(raw, dry, wet) { return Math.max(0, Math.min(100, (raw - dry) * 100 / (wet - dry))); }

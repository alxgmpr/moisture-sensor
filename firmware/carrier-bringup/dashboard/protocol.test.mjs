import {test} from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {DEFAULTS, encode, decode, validate, commands, crc32, decodeStatus, activity, moisture} from './protocol.mjs';
test('C and browser encode exactly the same bytes', () => {
  const c = {...DEFAULTS, name:'Fern'};
  const wire = encode(c);
  assert.deepEqual(decode(new DataView(wire.buffer)),c);
  assert.equal(Buffer.from(wire).toString('hex'),execFileSync(process.env.CONFIG_TEST_BIN,['--fixture'],{encoding:'utf8'}).trim());
});
test('writes fit default ATT MTU and cover all configuration bytes', () => {
  const wire=encode(DEFAULTS), packets=commands(wire), received=new Uint8Array(64);
  assert.deepEqual(packets[0],Uint8Array.of(1));
  for (const packet of packets.slice(1,-1)) {
    assert.ok(packet.length<=20); received.set(packet.slice(2),packet[1]);
  }
  assert.deepEqual(received,wire);
  assert.equal(new DataView(packets.at(-1).buffer).getUint32(1,true),crc32(wire));
  assert.equal(crc32(new TextEncoder().encode('123456789')),0xcbf43926);
});
test('invalid or unsafe settings cannot be encoded', () => {
  for (const override of [{name:'abcdefghijkl'}, {name:'é'}, {cycle:59}, {cycle:NaN},
    {window:1000}, {cycle:60,window:31000}, {advertising:5000}, {advertising:101},
    {session:901}, {lowCycle:800}, {lowMv:799}, {dry1:5658}, {wet2:200000}, {calibrated:1}]) {
    assert.throws(()=>encode({...DEFAULTS,...override}));
  }
  assert.doesNotThrow(()=>validate({...DEFAULTS, name:'',cycle:60,window:30000}));
  assert.doesNotThrow(()=>validate({...DEFAULTS, lowMv:800}));
  assert.doesNotThrow(()=>validate({...DEFAULTS, window:10000,advertising:1000,lowMv:2500}));
});
test('reject protocol drift, noncanonical data and short responses', () => {
  const wire=encode(DEFAULTS);wire[63]=1;
  assert.throws(()=>decode(new DataView(wire.buffer)));
  wire[63]=0;wire[0]=2;assert.throws(()=>decode(new DataView(wire.buffer)));
  assert.throws(()=>decodeStatus(new DataView(new ArrayBuffer(47))));
});
test('status has signed raw values and explicit persistence state', () => {
  const wire=new Uint8Array(48),v=new DataView(wire.buffer);wire[0]=1;wire[1]=7;
  v.setInt16(4,-1234,true);v.setInt32(8,-9000,true);v.setInt32(24,-5,true);
  const s=decodeStatus(v);assert.equal(s.temperature,-12.34);assert.equal(s.raw1,-9000);
  assert.equal(s.saveError,-5);assert.ok(s.valid&&s.stored&&s.saving);
});
test('cadence estimate and reverse calibration', () => {
  const a=activity(DEFAULTS);assert.equal(a.measurements,96);assert.ok(a.events<10&&a.events>9);
  assert.ok(a.perDay<960);assert.equal(moisture(150,200,100),50);
});

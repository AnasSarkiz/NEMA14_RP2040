/** Native CLI regression: preserve authored copper while routing the rest of a coupon. */
import {spawnSync} from 'node:child_process'
import {mkdirSync,copyFileSync} from 'node:fs'
const out='.config/authored-kelvin';mkdirSync(out,{recursive:true})
const env={...process.env,XDG_CONFIG_HOME:'.config'}
function run(bin:string,args:string[]){const r=spawnSync(bin,args,{env,stdio:'inherit',timeout:120000});if(r.error)throw r.error;if(r.status!==0)throw Error(`${bin} exited ${r.status}`)}
run('tsci',['build','experiments/kelvin/fixture.tsx','--routing-disabled'])
copyFileSync('dist/experiments/kelvin/fixture/circuit.json',out+'/authored.circuit.json')
run('tsci',['build','experiments/kelvin/fixture.tsx','--autorouter-timeout','60s'])
copyFileSync('dist/experiments/kelvin/fixture/circuit.json',out+'/routed.circuit.json')
run(process.env.PYTHON??'python3',['scripts/verify-authored-kelvin.py',out+'/authored.circuit.json',out+'/routed.circuit.json',out+'/verification.json'])

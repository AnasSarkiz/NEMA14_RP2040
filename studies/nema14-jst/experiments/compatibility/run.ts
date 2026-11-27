/** Run in a fresh Bun process; pass an installed, pinned stack's node_modules. */
import {plugin} from 'bun'
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
const [modulesArg,label,mode,out]=process.argv.slice(2)
if(!modulesArg||!['legacy','tagged','checker-only'].includes(label)||!['authored','automatic'].includes(mode)||!out)throw Error('Usage: bun experiments/compatibility/run.ts NODE_MODULES legacy|tagged|checker-only authored|automatic OUTPUT_PREFIX')
const modules=resolve(modulesArg),versions=Object.fromEntries(['@tscircuit/core','@tscircuit/checks','@tscircuit/capacity-autorouter','circuit-json'].map(n=>[n,JSON.parse(readFileSync(modules+'/'+n+'/package.json','utf8')).version]))
const expected:any={legacy:['0.0.2110','0.0.242','0.0.958','0.0.521'],tagged:['0.0.2488','0.0.283','0.0.1165','0.0.562'],'checker-only':['0.0.2110','0.0.283','0.0.958','0.0.562']}
if(JSON.stringify(Object.values(versions))!==JSON.stringify(expected[label]))throw Error('Stack version mismatch '+JSON.stringify(versions))
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {Circuit}=await import(pathToFileURL(modules+'/@tscircuit/core/dist/index.js').href)
const {default:Coupon}=await import('./one-shunt')
mkdirSync(resolve(out,'..'),{recursive:true});const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}})
c.on('autorouting:start',(e:any)=>writeFileSync(out+'.routing-input.json',JSON.stringify(e,null,2)+'\n'))
c.add(Coupon({authored:mode==='authored'}));const started=performance.now();await c.renderUntilSettled()
writeFileSync(out+'.circuit.json',JSON.stringify(c.getCircuitJson(),null,2)+'\n')
writeFileSync(out+'.receipt.json',JSON.stringify({label,mode,versions,elapsed_ms:performance.now()-started},null,2)+'\n')

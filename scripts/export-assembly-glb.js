// Retain indexed source meshes rather than expanding the verified Scene3D triangles.
import * as THREE from "three"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { GLTFExporter } from "three/examples/jsm/exporters/GLTFExporter.js"
import { createHash } from "node:crypto"
import { readFileSync, writeFileSync } from "node:fs"
const sha = (p) => createHash("sha256").update(readFileSync(p)).digest("hex")
globalThis.ProgressEvent ??= class { constructor(type, values = {}) {this.type=type;Object.assign(this,values)} }
globalThis.FileReader ??= class {
  async readAsArrayBuffer(blob) {this.result=await blob.arrayBuffer();this.onloadend?.({target:this})}
  async readAsDataURL(blob) {this.result=`data:${blob.type};base64,${Buffer.from(await blob.arrayBuffer()).toString("base64")}`;this.onloadend?.({target:this})}
}
const assets = JSON.parse(readFileSync("assets/assembly/asset-manifest.json", "utf8"))
if (!assets.tscircuit_native_Z_up_normalized) throw new Error("Assembly GLBs require native-frame normalization")
const models = JSON.parse(readFileSync("assets/assembly/models.json", "utf8"))
const root = new THREE.Group();root.name="NEMA14_INSTALLED_ASSEMBLY"
const loader = new GLTFLoader()
let meshes=0,triangles=0;const groupNames=[]
for (const [name,url] of Object.entries(models)) {
  const gltf=await loader.loadAsync(url)
  gltf.scene.name=name;root.add(gltf.scene);groupNames.push(name)
  gltf.scene.traverse((o)=>{if(o instanceof THREE.Mesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.getAttribute("position").count)/3}})
}
// Match the documented native tscircuit GLTF export frame: CAD(x,y,z)->(-x,z,y).
root.applyMatrix4(new THREE.Matrix4().set(-1,0,0,0, 0,0,1,0, 0,1,0,0, 0,0,0,1))
root.updateMatrixWorld(true)
const b=new THREE.Box3().setFromObject(root);const actual=[...b.min.toArray(),...b.max.toArray()]
const n=assets.native_mounted_bbox_mm;const expected=[-n[3],n[2],n[1],-n[0],n[5],n[4]]
if(actual.some((v,i)=>Math.abs(v-expected[i])>.08))throw new Error("Indexed GLB bounds/frame differ from native review")
const output=await new GLTFExporter().parseAsync(root,{binary:true,onlyVisible:true,trs:false})
if (!(output instanceof ArrayBuffer))throw new Error("Expected compact binary GLB")
writeFileSync("artifacts/assembly-scene/installed-assembly.glb",new Uint8Array(output))
writeFileSync("artifacts/assembly-scene/indexed-export-review.json",JSON.stringify({
  source_board_sha256:assets.source_board_sha256,asset_manifest_sha256:sha("assets/assembly/asset-manifest.json"),
  installed_glb_sha256:sha("artifacts/assembly-scene/installed-assembly.glb"),bytes:output.byteLength,
  group_names:groupNames,meshes,triangles,rendered_gltf_bounds_mm:actual,expected_gltf_bounds_mm:expected,
  indexed_source_meshes_retained:true,hardware_fit_verified:false,
},null,2)+"\n")
console.log("Compact GLB exported:",Math.round(output.byteLength/1024/1024),"MiB;",groupNames.length,"groups;",triangles,"triangles")

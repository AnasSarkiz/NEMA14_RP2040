import * as THREE from "three"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"

const canvas = document.querySelector("canvas")
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true})
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.setSize(innerWidth, innerHeight)
renderer.setClearColor(0xf5f6f8)
const scene = new THREE.Scene()
scene.add(new THREE.HemisphereLight(0xffffff, 0x626b78, 2.7))
const light = new THREE.DirectionalLight(0xffffff, 3.0)
light.position.set(70, 120, 60); scene.add(light)
const fill = new THREE.DirectionalLight(0xffffff, 1.8)
fill.position.set(-80, 40, -80); scene.add(fill)
const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, .1, 2000)
const controls = new OrbitControls(camera, renderer.domElement)
controls.enableDamping = false
controls.addEventListener("change", () => renderer.render(scene, camera))
let model
const status = document.querySelector("#status")
const views = {
  isometric: new THREE.Vector3(1, 1.05, 1.4),
  top: new THREE.Vector3(0, 1, 0),
  controller: new THREE.Vector3(.55, 1, .8),
  side: new THREE.Vector3(1, .05, .001),
  underside: new THREE.Vector3(1, -1, 1.4),
}
function setView(name) {
  if (!model) return
  const bb = name === "controller" ? new THREE.Box3(new THREE.Vector3(-18,-1,-18),new THREE.Vector3(18,10,18)) : new THREE.Box3().setFromObject(model)
  const center = bb.getCenter(new THREE.Vector3())
  const extent = bb.getSize(new THREE.Vector3())
  const distance = Math.max(extent.x, extent.y, extent.z) * 2.15
  camera.position.copy(center).addScaledVector(views[name], distance / views[name].length())
  camera.up.set(...(name === "top" ? [0,0,1] : [0,1,0]));camera.lookAt(center);controls.target.copy(center);controls.update();renderer.render(scene,camera)
}
for (const button of document.querySelectorAll("button[data-view]")) {
  button.onclick = () => setView(button.dataset.view)
}
new GLTFLoader().load("./installed-assembly.glb", (gltf) => {
  model = gltf.scene;scene.add(model)
  let meshes = 0, vertices = 0
  model.traverse((child) => {
    if (child instanceof THREE.Mesh) {meshes++;vertices += child.geometry.getAttribute("position").count}
  })
  const bb = new THREE.Box3().setFromObject(model)
  const bounds = [...bb.min.toArray(), ...bb.max.toArray()]
  const size = bb.getSize(new THREE.Vector3())
  status.textContent = `Loaded assembly · ${size.x.toFixed(1)} × ${size.z.toFixed(1)} × ${size.y.toFixed(1)} mm · drag to rotate, scroll to zoom`
  ;window.assemblyReview = {loaded: true, meshes, vertices, bounds, webgl: true, setView}
  setView("isometric")
}, undefined, (error) => {
  status.textContent = "Assembly model failed to load"
  ;window.assemblyReview = {loaded: false, error: String(error)}
  console.error(error)
})
window.onresize = () => {
  camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);renderer.render(scene,camera)
}
// Imported native CAD has thousands of meshes. Render only on view changes.
renderer.render(scene,camera)

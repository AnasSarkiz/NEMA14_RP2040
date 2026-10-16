import * as THREE from 'three'
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js'
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js'
const canvas=document.querySelector('canvas')
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true})
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor('#f2f4f5')
const scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xffffff,0x65706d,3))
for(const p of [[60,100,70],[-80,20,-50]]){const l=new THREE.DirectionalLight(0xffffff,2);l.position.set(...p);scene.add(l)}
const camera=new THREE.PerspectiveCamera(38,1,.1,1000), controls=new OrbitControls(camera,canvas)
controls.enableDamping=true
const views={complete:{p:[85,60,90],t:[5,-15,0]},connector:{p:[25,20,30],t:[7.4,6,12.85]},top:{p:[0,110,.01],t:[5,0,0]},side:{p:[105,5,0],t:[6,-15,0]},underside:{p:[65,-8,65],t:[0,-4,0]}}
function view(k){camera.position.set(...views[k].p);controls.target.set(...views[k].t);controls.update()}
new GLTFLoader().load('assembled.glb',g=>{scene.add(g.scene);view('complete');window.assemblyScene=g.scene;window.assemblyReady=true;document.querySelector('#loading').textContent=''},undefined,e=>{document.querySelector('#loading').textContent=String(e)})
for(const b of document.querySelectorAll('[data-view]'))b.addEventListener('click',()=>view(b.dataset.view))
function draw(){renderer.setSize(canvas.clientWidth,canvas.clientHeight,false);camera.aspect=canvas.clientWidth/canvas.clientHeight;camera.updateProjectionMatrix();controls.update();renderer.render(scene,camera);requestAnimationFrame(draw)}draw()

// 306 Doors — the corridor. A production-value restaging demonstration of Ulysses'
// "Reasonably available": the federal reading room as a hall at night, one door per
// address the law prints. Same committed census, embedded; every figure derived at load.
import * as THREE from 'three'

const D = JSON.parse(document.getElementById('census').textContent)
const A = D.addresses

/* ── verdicts ─────────────────────────────────────────────────────────────── */
function klass(a) {
  if (a.out === '2xx') return 'opened'
  if (a.out === 'blocked') return 'turned'
  if (a.out === 'network') return 'silent'
  return 'broken'
}
const VERDICT = {
  opened: 'The door opened.',
  broken: 'The door is bricked shut.',
  turned: 'The house turns a machine reader away.',
  silent: 'No one answers — the house is gone.',
}
const FLAG = { opened: 'OPENED', broken: 'BROKEN', turned: 'TURNED AWAY', silent: 'NO ANSWER' }
const failedTotal = A.filter((a) => klass(a) !== 'opened').length

/* ── scene ────────────────────────────────────────────────────────────────── */
const canvas = document.getElementById('c')
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
const scene = new THREE.Scene()
const NIGHT = 0x0e0c09
scene.background = new THREE.Color(NIGHT)
scene.fog = new THREE.Fog(NIGHT, 16, 110)

const camera = new THREE.PerspectiveCamera(58, 1, 0.1, 260)
const EYE = 3.0
camera.position.set(0, EYE, 8)

// hall: floor, ceiling glow line, walls implied by doors
const SPACING = 4.2
const PER_SIDE = Math.ceil(A.length / 2)
const HALL = PER_SIDE * SPACING + 40
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(26, HALL + 80),
  new THREE.MeshStandardMaterial({ color: 0x171310, roughness: 0.92, metalness: 0.05 }),
)
floor.rotation.x = -Math.PI / 2
floor.position.z = -HALL / 2
scene.add(floor)

// the hall itself: two walls and a ceiling, so the doors stand IN something
const wallMat = new THREE.MeshStandardMaterial({ color: 0x2b2318, roughness: 0.96 })
for (const s of [-1, 1]) {
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(HALL + 80, 8.2), wallMat)
  wall.rotation.y = s === -1 ? Math.PI / 2 : -Math.PI / 2
  wall.position.set(s * 7.15, 4.1, -HALL / 2)
  scene.add(wall)
}
const ceil = new THREE.Mesh(new THREE.PlaneGeometry(26, HALL + 80),
  new THREE.MeshStandardMaterial({ color: 0x1c1610, roughness: 1 }))
ceil.rotation.x = Math.PI / 2
ceil.position.set(0, 8.0, -HALL / 2)
scene.add(ceil)

// sparse warm bulbs down the hall — glow spheres plus a few real lights
const bulbGeo = new THREE.SphereGeometry(0.16, 10, 10)
const bulbMat = new THREE.MeshBasicMaterial({ color: 0xffe9bf })
for (let z = 2; z > -HALL - 10; z -= 14) {
  const b = new THREE.Mesh(bulbGeo, bulbMat)
  b.position.set(0, 7.2, z)
  scene.add(b)
  const pl = new THREE.PointLight(0xffdf9e, 14, 26, 1.7)
  pl.position.set(0, 6.8, z)
  scene.add(pl)
}
scene.add(new THREE.AmbientLight(0xfff0d8, 0.5))
scene.add(new THREE.HemisphereLight(0xffe9c4, 0x14100b, 0.35))
const key = new THREE.DirectionalLight(0xffe9c4, 0.4)
key.position.set(3, 10, 6)
scene.add(key)

/* ── doors ────────────────────────────────────────────────────────────────── */
const DOOR_W = 1.7, DOOR_H = 3.4, WALL_X = 6.4
const INK = { unknocked: 0x2a241d, opened: 0xa9b291, broken: 0xd14433, turned: 0xd89a2e, silent: 0x8598c2 }

const frameGeo = new THREE.BoxGeometry(DOOR_W + 0.5, DOOR_H + 0.5, 0.35)
const frameMat = new THREE.MeshStandardMaterial({ color: 0x35291c, roughness: 0.75 })
const frames = new THREE.InstancedMesh(frameGeo, frameMat, A.length)
const leafGeo = new THREE.BoxGeometry(DOOR_W, DOOR_H, 0.14)
const leafMat = new THREE.MeshStandardMaterial({ color: 0x8a7052, roughness: 0.6, metalness: 0.06 })
const leaves = new THREE.InstancedMesh(leafGeo, leafMat, A.length)
leaves.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(A.length * 3), 3)
// status lamp over each door
const lampGeo = new THREE.SphereGeometry(0.19, 12, 12)
const lampMat = new THREE.MeshBasicMaterial({ color: 0xffffff })
const lamps = new THREE.InstancedMesh(lampGeo, lampMat, A.length)
lamps.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(A.length * 3), 3)

const m4 = new THREE.Matrix4()
const doorPos = []
const state = A.map(() => 'unknocked')
const cLeaf = new THREE.Color(0x8a7052)
const cLamp = new THREE.Color(0x241f18)
for (let i = 0; i < A.length; i++) {
  const side = i % 2 === 0 ? -1 : 1
  const z = -8 - Math.floor(i / 2) * SPACING
  const x = side * WALL_X
  doorPos.push({ x, z, side })
  m4.makeRotationY(side === -1 ? Math.PI / 2 : -Math.PI / 2)
  m4.setPosition(x, DOOR_H / 2 + 0.25, z)
  frames.setMatrixAt(i, m4)
  leaves.setMatrixAt(i, m4)
  leaves.setColorAt(i, cLeaf)
  const lm = new THREE.Matrix4().makeTranslation(x - side * 0.1, DOOR_H + 0.85, z)
  lamps.setMatrixAt(i, lm)
  lamps.setColorAt(i, cLamp)
}
scene.add(frames, leaves, lamps)

/* the four misspellings: an alcove at the entrance, spotlit, before everything */
const canon = A.filter((a) => /archives\.gov/.test(a.u) && /ibr-locations|ibr_locations/.test(a.u) && klass(a) === 'opened')
const typos = []
A.forEach((a, i) => {
  if (/archives\.gov/.test(a.u) && klass(a) !== 'opened' && /ibr|federal-regster|crf/.test(a.u)) typos.push(i)
})
const spot = new THREE.SpotLight(0xffd9c9, 26, 30, 0.5, 0.55)
spot.position.set(0, 9, 2)
spot.target.position.set(0, 1.4, -2.5)
scene.add(spot, spot.target)
// pull the four typo doors out of the rows and stand them at the entrance, facing the visitor
typos.forEach((idx, k) => {
  const x = -4.6 + k * 3.06
  const z = -2.6
  doorPos[idx] = { x, z, side: 0, exhibit: true }
  m4.makeRotationY(0)
  m4.setPosition(x, DOOR_H / 2 + 0.25, z)
  frames.setMatrixAt(idx, m4)
  leaves.setMatrixAt(idx, m4)
  const lm = new THREE.Matrix4().makeTranslation(x, DOOR_H + 0.85, z)
  lamps.setMatrixAt(idx, lm)
})
frames.instanceMatrix.needsUpdate = true
leaves.instanceMatrix.needsUpdate = true
lamps.instanceMatrix.needsUpdate = true

// typo letters floating over the exhibit doors, drawn once on canvas textures
function typoSprite(text, x, z) {
  const cv = document.createElement('canvas')
  cv.width = 512; cv.height = 160
  const g = cv.getContext('2d')
  g.font = '700 64px ui-monospace, Menlo, monospace'
  g.textAlign = 'center'
  g.fillStyle = '#c0392b'
  g.fillText(text, 256, 96)
  const tx = new THREE.CanvasTexture(cv)
  tx.colorSpace = THREE.SRGBColorSpace
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tx, transparent: true }))
  sp.scale.set(3.4, 1.06, 1)
  sp.position.set(x, DOOR_H + 1.7, z)
  scene.add(sp)
}
const TYPO_LABEL = { 'ibr_zlocations': 'ibr_→z←locations', 'ibrlocations': 'ibr→‸←locations', '/crf/': '/c→rf←/', 'federal-regster': 'federal-reg→‸←ster' }
typos.forEach((idx) => {
  const u = A[idx].u
  const key2 = Object.keys(TYPO_LABEL).find((k) => u.includes(k.replaceAll('/', '')) || u.includes(k))
  const p = doorPos[idx]
  typoSprite(key2 ? TYPO_LABEL[key2] : 'typo', p.x, p.z)
})

/* ── knocking ─────────────────────────────────────────────────────────────── */
const tallies = { opened: 0, broken: 0, turned: 0, silent: 0 }
let walkedN = 0
const leafColor = {
  opened: new THREE.Color(INK.opened), broken: new THREE.Color(INK.broken),
  turned: new THREE.Color(INK.turned), silent: new THREE.Color(INK.silent),
}
function knock(i, quiet) {
  if (state[i] !== 'unknocked') { if (!quiet) showCard(i); return }
  const k = klass(A[i])
  state[i] = k
  tallies[k]++; walkedN++
  leaves.setColorAt(i, leafColor[k])
  lamps.setColorAt(i, leafColor[k])
  leaves.instanceColor.needsUpdate = true
  lamps.instanceColor.needsUpdate = true
  if (k === 'opened') {
    // an opened door swings: replace its leaf rotation by an ajar angle
    const p = doorPos[i]
    const rotY = p.side === 0 ? -0.9 : (p.side === -1 ? Math.PI / 2 - 0.9 : -Math.PI / 2 + 0.9)
    m4.makeRotationY(rotY)
    m4.setPosition(p.x, DOOR_H / 2 + 0.25, p.z)
    leaves.setMatrixAt(i, m4)
    leaves.instanceMatrix.needsUpdate = true
  }
  tick(k)
  renderHud()
  if (!quiet) showCard(i)
}

// a synthesized knock — two short taps, pitch by verdict; no assets, WebAudio only
let AC = null
function tick(k) {
  try {
    AC = AC || new (window.AudioContext || window.webkitAudioContext)()
    const t0 = AC.currentTime
    const freq = k === 'opened' ? 190 : k === 'broken' ? 88 : k === 'turned' ? 130 : 60
    for (const dt of [0, 0.14]) {
      const o = AC.createOscillator(), g = AC.createGain()
      o.type = 'triangle'; o.frequency.value = freq
      g.gain.setValueAtTime(0.0001, t0 + dt)
      g.gain.exponentialRampToValueAtTime(0.12, t0 + dt + 0.008)
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dt + 0.16)
      o.connect(g).connect(AC.destination)
      o.start(t0 + dt); o.stop(t0 + dt + 0.2)
    }
  } catch { /* sound is a garnish, never a dependency */ }
}

/* ── HUD ──────────────────────────────────────────────────────────────────── */
const hudWalked = document.getElementById('hud-walked')
const hudRows = document.getElementById('hud-rows')
function renderHud() {
  hudWalked.textContent = walkedN
  hudRows.replaceChildren()
  for (const [k, label] of [['opened', 'opened'], ['broken', 'bricked shut'], ['turned', 'turned you away'], ['silent', 'no answer']]) {
    const r = document.createElement('div')
    r.className = 'hud-row'
    const d = document.createElement('span'); d.className = 'hud-dot ' + k
    const l = document.createElement('span'); l.textContent = label; l.className = 'hud-k'
    const n = document.createElement('span'); n.textContent = tallies[k]; n.className = 'hud-n'
    r.append(d, l, n); hudRows.append(r)
  }
}
renderHud()

/* ── the card (scene overlay) ─────────────────────────────────────────────── */
const card = document.getElementById('card')
function showCard(i) {
  const a = A[i], k = klass(a)
  const sec = a.secs[0], meta = D.sections[sec]
  const more = a.secs.length > 1 ? ` and ${a.secs.length - 1} other section${a.secs.length > 2 ? 's' : ''}` : ''
  let after
  if (k === 'opened') after = a.final && a.final !== a.u ? `It opened, after redirecting to ${a.final}` : 'It simply opened. Most do — that is the texture of the hall.'
  else if (a.arch && a.arch.last200) {
    const s = a.arch.last200
    after = `The law’s address fails, but a public archive still holds a copy — last saved ${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}. The Internet Archive is a charity; the obligation is the law’s.`
  } else after = 'No public archive copy answered either. “Reasonably available” is, for this section, a claim with nothing behind it.'
  card.className = 'card is-' + k
  card.innerHTML = ''
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; card.append(n); return n }
  el('p', 'card-no', `DOOR ${i + 1} OF ${A.length} · ${a.host}` )
  el('p', 'card-binds', `${sec}${meta && meta.h ? ' — “' + meta.h + '”' : ''}${more} makes a document behind this address binding.`)
  if (meta && meta.cita) el('p', 'card-cita', 'citation of record: ' + meta.cita)
  el('p', 'card-url', a.printed[0] || a.u)
  el('p', 'card-answer', `${VERDICT[k]}  ${a.s1 ? 'HTTP ' + a.s1 + (a.s2 ? ' · asked again: ' + a.s2 : '') : (a.e1 ? String(a.e1).slice(0, 52) : '')}`)
  el('p', 'card-after', after)
  const x = el('button', 'card-x', '× close')
  x.addEventListener('click', hideCard)
  card.hidden = false
}
function hideCard() { card.hidden = true }
addEventListener('keydown', (e) => { if (e.key === 'Escape') hideCard() })

/* ── walking: wheel / touch / keys move the camera down the hall ─────────── */
let targetZ = 8, curZ = 8
const MINZ = -HALL - 4, MAXZ = 8
addEventListener('wheel', (e) => {
  targetZ = Math.max(MINZ, Math.min(MAXZ, targetZ - e.deltaY * 0.02))
}, { passive: true })
let touchY = null
addEventListener('touchstart', (e) => { touchY = e.touches[0].clientY }, { passive: true })
addEventListener('touchmove', (e) => {
  if (touchY === null) return
  targetZ = Math.max(MINZ, Math.min(MAXZ, targetZ + (e.touches[0].clientY - touchY) * 0.045))
  touchY = e.touches[0].clientY
}, { passive: true })
addEventListener('keydown', (e) => {
  if (e.key === 'ArrowUp' || e.key === 'w') targetZ = Math.max(MINZ, targetZ - 3.4)
  if (e.key === 'ArrowDown' || e.key === 's') targetZ = Math.min(MAXZ, targetZ + 3.4)
})

/* ── picking ──────────────────────────────────────────────────────────────── */
const ray = new THREE.Raycaster()
const ptr = new THREE.Vector2()
let hover = -1
canvas.addEventListener('pointermove', (e) => {
  ptr.x = (e.clientX / innerWidth) * 2 - 1
  ptr.y = -(e.clientY / innerHeight) * 2 + 1
})
canvas.addEventListener('click', () => { if (hover >= 0) knock(hover) })

/* ── knock on all: a wave that walks the hall ─────────────────────────────── */
const btnAll = document.getElementById('all')
btnAll.addEventListener('click', () => {
  btnAll.disabled = true
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
  let i = 0
  const step = () => {
    const batch = reduced ? A.length : 9
    for (let b = 0; b < batch && i < A.length; b++, i++) {
      if (state[i] === 'unknocked') {
        const k = klass(A[i]); state[i] = k; tallies[k]++; walkedN++
        leaves.setColorAt(i, leafColor[k]); lamps.setColorAt(i, leafColor[k])
        if (k === 'opened') {
          const p = doorPos[i]
          const rotY = p.side === 0 ? -0.9 : (p.side === -1 ? Math.PI / 2 - 0.9 : -Math.PI / 2 + 0.9)
          m4.makeRotationY(rotY); m4.setPosition(p.x, DOOR_H / 2 + 0.25, p.z)
          leaves.setMatrixAt(i, m4)
        }
      }
    }
    leaves.instanceColor.needsUpdate = true
    lamps.instanceColor.needsUpdate = true
    leaves.instanceMatrix.needsUpdate = true
    renderHud()
    if (i < A.length) requestAnimationFrame(step)
    else document.getElementById('hud-note').textContent =
      `${A.length - failedTotal} opened · ${failedTotal} did not — probed 14 August 2026, every failure asked twice.`
  }
  step()
})

document.getElementById('one').addEventListener('click', () => {
  const pool = []
  for (let i = 0; i < A.length; i++) if (state[i] === 'unknocked') pool.push(i)
  const i = pool.length ? pool[Math.floor(Math.random() * pool.length)] : Math.floor(Math.random() * A.length)
  // walk the camera to that door, then knock
  targetZ = Math.min(MAXZ, Math.max(MINZ, doorPos[i].z + 5.4))
  setTimeout(() => knock(i), 650)
})

/* ── intro fade ───────────────────────────────────────────────────────────── */
const intro = document.getElementById('intro')
let introGone = false
function dismissIntro() {
  if (introGone) return
  introGone = true
  intro.classList.add('gone')
}
addEventListener('wheel', dismissIntro, { passive: true, once: false })
document.getElementById('enter').addEventListener('click', () => { dismissIntro(); targetZ = 5.2 })

/* ── frame loop ───────────────────────────────────────────────────────────── */
function resize() {
  renderer.setSize(innerWidth, innerHeight, false)
  camera.aspect = innerWidth / innerHeight
  camera.updateProjectionMatrix()
}
addEventListener('resize', resize)
resize()

const tmpM = new THREE.Matrix4()
function frame() {
  curZ += (targetZ - curZ) * 0.07
  camera.position.z = curZ
  camera.position.x = Math.sin(curZ * 0.10) * 0.35
  // hover highlight
  ray.setFromCamera(ptr, camera)
  const hit = ray.intersectObject(leaves, false)[0]
  const h = hit ? hit.instanceId : -1
  if (h !== hover) {
    document.body.style.cursor = h >= 0 ? 'pointer' : 'default'
    hover = h
  }
  renderer.render(scene, camera)
  requestAnimationFrame(frame)
}
frame()

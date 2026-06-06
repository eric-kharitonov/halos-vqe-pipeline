import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

/*
 * Stylized 3D concept of the engineered D. radiodurans cell. This is an ILLUSTRATION,
 * not a physical simulation — a translucent membrane you can rotate and zoom into, with
 * the inserted gene (DNA helix), surface metal-binding proteins capturing mobile ions,
 * and a nucleated crystal. Deliberately distinct from the real-data 3D (the ESMFold
 * protein in Protein3D.tsx), which shows actual predicted structure.
 */

const CYAN = 0x48e3ea
const GREEN = 0x6ad08f
const AMBER = 0xf5a623

export default function CellViewer3D() {
  const mountRef = useRef<HTMLDivElement>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    } catch {
      setFailed(true)
      return
    }

    const width = mount.clientWidth || 600
    const height = mount.clientHeight || 380
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    mount.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0.4, 5)

    scene.add(new THREE.AmbientLight(0xffffff, 1.4))
    const dir = new THREE.DirectionalLight(0xffffff, 1.1)
    dir.position.set(3, 4, 5)
    scene.add(dir)

    // ---- membrane: translucent ellipsoid + wireframe overlay ----
    const cell = new THREE.Group()
    const RX = 1.55, RY = 1.2, RZ = 1.2
    const membraneGeo = new THREE.SphereGeometry(1, 48, 32)
    const membrane = new THREE.Mesh(
      membraneGeo,
      new THREE.MeshStandardMaterial({ color: GREEN, transparent: true, opacity: 0.1, roughness: 0.5, side: THREE.DoubleSide }),
    )
    membrane.scale.set(RX, RY, RZ)
    cell.add(membrane)
    const wire = new THREE.LineSegments(
      new THREE.WireframeGeometry(new THREE.SphereGeometry(1, 18, 12)),
      new THREE.LineBasicMaterial({ color: GREEN, transparent: true, opacity: 0.16 }),
    )
    wire.scale.set(RX, RY, RZ)
    cell.add(wire)

    // ---- inserted gene: DNA double helix ----
    const helix = new THREE.Group()
    const turns = 3, perTurn = 14, N = turns * perTurn, hr = 0.22, hh = 1.35
    const beadGeo = new THREE.SphereGeometry(0.04, 10, 10)
    const beadMat = new THREE.MeshStandardMaterial({ color: CYAN, emissive: CYAN, emissiveIntensity: 0.5 })
    const rungMat = new THREE.MeshStandardMaterial({ color: CYAN, transparent: true, opacity: 0.4 })
    for (let i = 0; i < N; i++) {
      const t = i / (N - 1)
      const a = t * turns * Math.PI * 2
      const y = (t - 0.5) * hh
      const A = new THREE.Vector3(Math.cos(a) * hr, y, Math.sin(a) * hr)
      const B = new THREE.Vector3(Math.cos(a + Math.PI) * hr, y, Math.sin(a + Math.PI) * hr)
      const sa = new THREE.Mesh(beadGeo, beadMat); sa.position.copy(A); helix.add(sa)
      const sb = new THREE.Mesh(beadGeo, beadMat); sb.position.copy(B); helix.add(sb)
      if (i % 2 === 0) {
        const mid = A.clone().add(B).multiplyScalar(0.5)
        const rung = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, A.distanceTo(B), 6), rungMat)
        rung.position.copy(mid)
        rung.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), B.clone().sub(A).normalize())
        helix.add(rung)
      }
    }
    helix.rotation.z = 0.3
    cell.add(helix)

    // ---- surface binding proteins + captured ions ----
    const protMat = new THREE.MeshStandardMaterial({ color: CYAN, emissive: CYAN, emissiveIntensity: 0.25 })
    const ionMat = new THREE.MeshStandardMaterial({ color: AMBER, emissive: AMBER, emissiveIntensity: 0.6 })
    const dirs = [
      new THREE.Vector3(1, 0.2, 0.3), new THREE.Vector3(-0.8, 0.5, 0.4),
      new THREE.Vector3(0.3, -0.7, 0.6), new THREE.Vector3(-0.4, -0.3, -0.9),
      new THREE.Vector3(0.6, 0.6, -0.5), new THREE.Vector3(-0.2, 0.9, -0.2),
    ]
    dirs.forEach(d => {
      d.normalize()
      const surf = new THREE.Vector3(d.x * RX, d.y * RY, d.z * RZ)
      const cone = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.24, 10), protMat)
      cone.position.copy(surf).add(d.clone().multiplyScalar(0.12))
      cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d)
      cell.add(cone)
      const ion = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 12), ionMat)
      ion.position.copy(surf).add(d.clone().multiplyScalar(0.3))
      cell.add(ion)
    })

    // ---- nucleated crystal (biomineral output) ----
    const crystal = new THREE.Group()
    const xtalGeo = new THREE.OctahedronGeometry(0.42, 0)
    crystal.add(new THREE.Mesh(xtalGeo, new THREE.MeshStandardMaterial({ color: CYAN, transparent: true, opacity: 0.28, roughness: 0.2 })))
    crystal.add(new THREE.LineSegments(new THREE.EdgesGeometry(xtalGeo), new THREE.LineBasicMaterial({ color: CYAN })))
    crystal.position.set(RX * 0.78, -RY * 0.5, RZ * 0.55)
    crystal.scale.set(1, 1.4, 1)
    cell.add(crystal)

    scene.add(cell)

    // ---- mobile ions drifting toward the cell ----
    const ions: THREE.Mesh[] = []
    const ionGeo = new THREE.SphereGeometry(0.05, 8, 8)
    for (let i = 0; i < 7; i++) {
      const m = new THREE.Mesh(ionGeo, ionMat)
      const reset = () => {
        const r = 2.6 + Math.random() * 1.6
        const th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1)
        m.position.set(r * Math.sin(ph) * Math.cos(th), r * Math.cos(ph) * 0.6, r * Math.sin(ph) * Math.sin(th))
      }
      reset()
      ;(m as unknown as { _reset: () => void })._reset = reset
      scene.add(m)
      ions.push(m)
    }

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.08
    controls.enablePan = false
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.7
    controls.minDistance = 2.2
    controls.maxDistance = 9

    // pause rendering when the canvas is offscreen
    let visible = true
    const io = new IntersectionObserver(es => { visible = es[0].isIntersecting }, { threshold: 0.01 })
    io.observe(mount)

    const ro = new ResizeObserver(() => {
      const w = mount.clientWidth, h = mount.clientHeight
      if (!w || !h) return
      camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h)
    })
    ro.observe(mount)

    let raf = 0
    const animate = () => {
      raf = requestAnimationFrame(animate)
      if (!visible) return
      helix.rotation.y += 0.01
      crystal.rotation.y += 0.004
      ions.forEach(m => {
        m.position.multiplyScalar(0.995)                       // drift inward
        if (m.position.length() < 1.5) (m as unknown as { _reset: () => void })._reset()
      })
      controls.update()
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect(); ro.disconnect(); controls.dispose()
      scene.traverse(o => {
        const mesh = o as THREE.Mesh
        if (mesh.geometry) mesh.geometry.dispose()
        const mat = mesh.material
        if (Array.isArray(mat)) mat.forEach(m => m.dispose())
        else if (mat) (mat as THREE.Material).dispose()
      })
      renderer.dispose()
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement)
    }
  }, [])

  if (failed) {
    return (
      <div className="flex h-[380px] w-full flex-col items-center justify-center gap-2 border border-halos-line bg-halos-bg p-4 text-center">
        <div className="font-mono text-[11px] tracking-widest text-halos-warn">3D VIEW UNAVAILABLE</div>
        <div className="max-w-xs font-mono text-[10px] leading-relaxed text-halos-muted">
          WebGL isn't available in this browser. The cell is a concept illustration either way.
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-[380px] w-full overflow-hidden border border-halos-line bg-halos-bg">
      <div ref={mountRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute bottom-2 left-2 font-mono text-[9px] tracking-widest text-halos-muted">
        DRAG TO ROTATE · SCROLL TO ZOOM · CONCEPT — STYLIZED, NOT A SIMULATION
      </div>
    </div>
  )
}

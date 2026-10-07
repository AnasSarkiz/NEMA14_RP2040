import catalog from "./jlcpcb-catalog.json"
import type { CadModelProp } from "@tscircuit/props"

// Supplier imports retain their full TSX/OBJ/STEP files under imports/.
// Preserve the checked board land pattern and pin aliases when attaching CAD.
// Supplier meshes are mirrored in this GitHub repository for the saved registry preview.
export function jlcProps(reference: string) {
  const id = (catalog.components as Record<string,string>)[reference]
  if (!id) return {}
  const part = (catalog.parts as Record<string, typeof catalog.parts[keyof typeof catalog.parts]>)[id]
  return {
    manufacturerPartNumber: part.manufacturerPartNumber,
    supplierPartNumbers: part.supplierPartNumbers,
    cadModel: { ...part.cadModel,
      ...(reference === "J_PD" ? {positionOffset:{x:-1.46,y:0,z:0}} :
          reference === "J_DATA" ? {positionOffset:{x:1.46,y:0,z:0}} : {}),
    } as CadModelProp,
  }
}

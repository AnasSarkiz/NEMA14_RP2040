import React from "react"
import Nema14Controller from "../index.circuit"

// Verify source nets without rerouting the qualified PCB.
export default function NetlistSource() {
  return <Nema14Controller routingDisabled={true} />
}

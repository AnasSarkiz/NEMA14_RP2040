import { readFileSync, writeFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { getSideEntryPlug } from '../src/side-entry-plug'
const data=readFileSync(process.argv[2])
writeFileSync(process.argv[3],JSON.stringify({board_sha256:createHash('sha256').update(data).digest('hex'),...getSideEntryPlug(JSON.parse(data.toString()))},null,2)+'\n')

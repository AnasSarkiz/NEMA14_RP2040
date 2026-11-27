/** Only the Bun plugin API used by the optional local-asset profiler. */
declare module 'bun' {
 export function plugin(definition: {
  name: string
  setup(builder: {
   onLoad(options: {filter: RegExp}, callback: (args: {path: string}) => {contents: string, loader: 'js'}): void
  }): void
 }): void
}

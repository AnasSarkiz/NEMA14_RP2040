# Portable viewer assets

The HTML embeds the installed @tscircuit/runframe 0.0.2929 standalone preview,
all OBJ meshes referenced by the saved V2 Circuit JSON, and the following
upstream assets. Its only bundle substitutions replace font CDN transport with
embedded data URLs. No PCB coordinates, nets or footprints are modified.

- Manifold 3.2.1 loader and WASM: https://cdn.jsdelivr.net/npm/manifold-3d@3.2.1/ (Apache-2.0; LICENSE retained).
- Unicode font resolver 1.0.1 Latin index, metadata and Noto Sans normal 400/700 WOFF: https://cdn.jsdelivr.net/gh/lojjic/unicode-font-resolver@v1.0.1/packages/data/ . Noto Sans uses the SIL Open Font License; OFL.txt retained.
- The native 3D view receives the embedded Manifold factory through its supported window.ManifoldModule hook.

The cloud workspace has no inbound forwarding route to the user's localhost.
The portable viewer is a display artifact, never a manufacturing release.

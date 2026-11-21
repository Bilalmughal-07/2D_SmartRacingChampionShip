# UI Design Specification

## Visual system

- Target window: 1440x900, with a verified responsive layout at 1280x720.
- Background: deep navy; panels: slate-blue; primary action: cyan; success: emerald; warning: amber; danger: rose.
- Racing roads use layered asphalt, shoulders, dashed lane markings, barriers, directional arrows, and status overlays; shortcuts use purple emphasis; checkpoints use numbered gates; start/finish use green/red; services use distinct icons.
- Text uses system Consolas fonts with large headings and readable body labels.

## Screen contract

| Screen | Required content | Current controls |
|---|---|---|
| Main Menu | entry points, project title, controls | keys 1-5, Enter |
| Track Explorer | interactive graph, selectable start/destination, checkpoint-safe route, arrows, zoom/pan/hover, legend, exact metrics, fuel/nitro recommendations, four-preset comparison | mouse vertex selection, right-drag pan, wheel/+/− zoom, algorithm/preset controls, live closure reroute |
| Racing | roads, themed environment, oriented cars, camera, minimap, time, lap/checkpoint, fuel/nitro, standings, event feed | W/S throttle/brake, A/D junction choice, Enter confirm, Space nitro, R refuel, P pause, M minimap |
| Algorithm Lab | shared route output and counters | Dijkstra result/counters baseline |
| Dashboard | standings and points | headless championship output + screen |

## Visual verification

The verification harness initializes Pygame with `SDL_VIDEODRIVER=dummy`, renders every screen against the real `GameApp._draw` path at both supported sizes, saves PNGs under `docs/screenshots/`, and inspects them for clipping/overlap. Real display smoke was previously confirmed with `pygame-ce 2.5.8`.

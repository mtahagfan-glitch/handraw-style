# Source thread

Mirage (@trymirage), 6 November 2026: https://x.com/trymirage/status/2118749777814774248

The opening post carries the 13 second shot (1920x1080).

> No video models were used in the making of this scene.
>
> Here's how we're building realistic 3D scenes in Claude with Tesseract, thread below.

> 1/ Reference. One still from GPT Image 2.6: a messy 80s kitchen, rainy night, full moon. Claude Code solved its camera from the vanishing points (21 mm lens, eye height 134 cm) so the 3D room lines up with the picture.

> 2/ Build. Claude Code wrote scripts that build the room in Tesseract: cabinets, appliances, props, materials and lights, with GPT Image 2.6 making textures to match. Two AI critic agents compared every round to the reference and sent back fix lists.

> 3/ Animate. A slow push-in. The microwave turntable spins as the display counts down; at :00 it beeps three times and the lamp goes out. Rain falls at three depths. The lightning is real light in the scene, and in the close strike a creature stands in the yard.

> 4/ Sound and render. Rain, thunder and the microwave hum are ElevenLabs sound effects, the beeps are synthesized, and the thunder is timed to each flash's distance. Path-traced at 128 samples per pixel in 1080p: about 45 min for 312 frames on one RTX PRO 6000.

> 5/ Proof it's 3D: the shot opens as grey clay, then a wipe reveals the render. Honest cheats: the yard is a relit 2D backplate, and the rain and the creature are 2D cards. The shot is one editable Tesseract file, so you can move the camera and re-render.

## How each post maps to the skill

| Post | Step in SKILL.md |
| --- | --- |
| 1/ Reference | 1 Reference still, 2 Solve the camera (`scripts/solve_camera.py`) |
| 2/ Build | 3 Build |
| 3/ Animate | 4 Animate |
| 4/ Sound and render | 5 Sound, 6 Render |
| 5/ Proof | 7 Proof and honesty |

The figures in the thread (lens, eye height, render time) are Mirage's own and were not checked independently.

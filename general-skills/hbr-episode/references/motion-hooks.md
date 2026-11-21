# Moving shots (hook and climax)

Parallax gives depth, not action. For the 2–3 moments the story hangs on (the hook, the goal, the sprint), turn
the drawing into real motion.

1. Pick a drawing with a clear action (a kick, a sprint, a crowd rising). Upscaled plate as input.
2. `python3 "$SK/scripts/motion.py" plates/NN/plate.jpg veo/NN.mp4 "slow push-in, the player sprints and
   reaches the ball, flags wave in the stand, hand-drawn ink style, no new objects" --model kling --dur 5`
   - Prompt = camera + what moves. The style comes from the picture. Add "no text, no new people".
   - Kling is cheaper; Veo (`--model veo`) is better at physics. Review before using; regenerate once at most.
   - Or hand the owner a prompt for Google Flow (Veo) with the plate; they download the clip.
3. Splice over the parallax scene, keeping the scene's exact frame count, so the action peaks on the spoken word:
   ```sh
   ffmpeg -i video/NN.mp4 -i veo/NN.mp4 -filter_complex "[0]trim=0:A,setpts=PTS-STARTPTS,fps=25,format=yuv420p,settb=1/25[a];\
   [1]scale=1920:1080:flags=lanczos,trim=0:D,setpts=PTS-STARTPTS,fps=25,format=yuv420p,settb=1/25[b];\
   [a][b]xfade=transition=fade:duration=0.3:offset=A-0.3,tpad=stop_mode=clone:stop=-1,trim=end_frame=N[v]" \
   -map "[v]" -c:v libx264 -crf 16 -pix_fmt yuv420p -r 25 video/NN_new.mp4
   ```
   A = where the clip starts in the scene (word time − clip action time), D = clip length, N = scene frames.
   Back up the parallax version first; after any re-render, splice again.
4. The hook: the first 3 seconds must move. Open on a moving shot or a fast push-in, never on a static frame.

// node depth_run.cjs <ort_path> <model.onnx> <in.f32> <W> <H> <out.f32>
const [ortPath, model, inp, W, H, out] = process.argv.slice(2);
const ort = require(ortPath); const fs = require('fs');
(async () => {
  const s = await ort.InferenceSession.create(model);
  const buf = fs.readFileSync(inp);
  const data = new Float32Array(buf.buffer, buf.byteOffset, buf.length / 4);
  const t = new ort.Tensor('float32', data, [1, 3, +H, +W]);
  const r = await s.run({ [s.inputNames[0]]: t });
  const o = r[s.outputNames[0]];
  fs.writeFileSync(out, Buffer.from(o.data.buffer)); console.log(o.dims.join('x'));
})();

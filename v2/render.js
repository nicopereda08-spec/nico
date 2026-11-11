// Step 2: render scene.html frame by frame and mux with the voiceover.
// Usage: node v2/render.js [fps] [only-these-seconds,comma-separated → PNG stills]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const dir = __dirname, build = path.join(dir, 'build');
const tl = JSON.parse(fs.readFileSync(path.join(build, 'timeline.json')));
const fps = +(process.argv[2] || 30), stills = process.argv[3];
(async () => {
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  await page.goto('file://' + path.join(dir, 'scene.html'));
  await page.evaluate(async t => { await document.fonts.ready; init(t); }, tl);
  if (stills) {
    for (const s of stills.split(',')) {
      await page.evaluate(t => seek(t), +s);
      await page.screenshot({ path: path.join(build, `still_${s}.png`) });
    }
    return b.close();
  }
  const out = path.join(dir, '..', 'out', 'video_en_v2_screen.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-i', path.join(build, 'voice.wav'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
    '-af', 'loudnorm=I=-15:TP=-1.5,aresample=48000', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.ceil(tl.total * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => seek(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await b.close(); console.log(out);
})();

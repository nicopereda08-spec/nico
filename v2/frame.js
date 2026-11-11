// Renders the static vertical background (with laptop) and caption layer, then composites the screen video into it.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const { execFileSync } = require('child_process');
(async () => {
  const b = await chromium.launch(); const page = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  const html = fs.readFileSync(path.join(__dirname, 'frame.html'), 'utf8');
  for (const [mode, file] of [['bg', 'bg.png'], ['', 'cap.png']]) {
    fs.writeFileSync(path.join(__dirname, '_f.html'), html.replace('MODE', mode));
    await page.goto('file://' + path.join(__dirname, '_f.html')); await page.evaluate(() => document.fonts.ready);
    if (!mode) await page.evaluate(() => document.querySelectorAll('.lid,.deck,.keys,.pad').forEach(e => e.remove()));
    await page.screenshot({ path: path.join(__dirname, 'build', file), omitBackground: !mode });
  }
  fs.unlinkSync(path.join(__dirname, '_f.html')); await b.close();
  const out = path.join(__dirname, '..', 'out', 'video_es_v2_vertical.mp4'), B = path.join(__dirname, 'build');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-loop', '1', '-i', `${B}/bg.png`,
    '-i', path.join(__dirname, '..', 'out', 'video_es_v2_screen.mp4'), '-loop', '1', '-i', `${B}/cap.png`,
    '-filter_complex', '[1:v]scale=980:551,eq=brightness=0.02:saturation=1.05[s];[0:v][s]overlay=50:660:shortest=1[a];[a][2:v]overlay=0:0:shortest=1,format=yuv420p[v]',
    '-map', '[v]', '-map', '1:a', '-c:v', 'libx264', '-crf', '19', '-c:a', 'copy', '-r', '30', '-movflags', '+faststart', out]);
  console.log(out);
})();

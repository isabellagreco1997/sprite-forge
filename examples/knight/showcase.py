"""1080p showcase: idle → walk (scrolling floor + parallax pillars) → idle, torch flicker, title. PIL frames → ffmpeg."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, random, sys

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else 'show'
os.makedirs(OUT, exist_ok=True)
FPS = 30; DUR = 10.0; N = int(DUR * FPS)
SC = 20                                   # sprite scale → 640x800
idle = [Image.open(f'out/frames/idle_{i}.png').convert('RGBA') for i in range(6)]
walk = [Image.open(f'out/frames/walk_{i}.png').convert('RGBA') for i in range(6)]
up = lambda im: im.resize((im.width * SC, im.height * SC), Image.NEAREST)
idle = [up(i) for i in idle]; walk = [up(i) for i in walk]
def _font(size):
    """Press Start 2P if installed (any OS font dir), else a monospace system font, else PIL's default."""
    for cand in (os.path.expanduser('~/Library/Fonts/PressStart2P-Regular.ttf'), 'PressStart2P-Regular.ttf',
                 '/System/Library/Fonts/Menlo.ttc', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 'C:/Windows/Fonts/consolab.ttf'):
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue
    return ImageFont.load_default()
font = _font(64)
font_s = _font(22)
random.seed(7)

# static background: dark stone gradient + vignette, built once
bg = Image.new('RGB', (1920, 1080), (16, 14, 22))
d = ImageDraw.Draw(bg)
for y in range(1080):
    k = y / 1080
    d.line([(0, y), (1920, y)], fill=(int(16 + 18 * k), int(14 + 12 * k), int(22 + 20 * k)))
FLOOR_Y = 900
d.rectangle([0, FLOOR_Y, 1920, 1080], fill=(26, 22, 30))
vig = Image.new('L', (1920, 1080), 0)
ImageDraw.Draw(vig).ellipse([-300, -250, 2220, 1330], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(220))
black = Image.new('RGB', (1920, 1080), (0, 0, 0))
bg = Image.composite(bg, black, vig)

# pillars (parallax): x positions in world space, 2 depth layers
pillars_far = [(i * 520 + 100) for i in range(8)]
pillars_near = [(i * 900 + 400) for i in range(6)]

def phase(t):
    """returns (mode, frame, walk_speed_px_per_s)"""
    if t < 2.6: return 'idle', int(t * 7) % 6, 0
    if t < 7.6: return 'walk', int((t - 2.6) * 9) % 6, 380
    return 'idle', int((t - 7.6) * 7) % 6, 0

scroll = 0.0
for i in range(N):
    t = i / FPS
    mode, fi, spd = phase(t)
    scroll += spd / FPS
    im = bg.copy()
    d = ImageDraw.Draw(im)
    # far pillars
    for px in pillars_far:
        x = (px - scroll * 0.25) % 2400 - 240
        d.rectangle([x, 120, x + 70, FLOOR_Y], fill=(30, 26, 38))
        d.rectangle([x, 120, x + 70, 150], fill=(38, 33, 46))
    # near pillars
    for px in pillars_near:
        x = (px - scroll * 0.6) % 3000 - 300
        d.rectangle([x, 40, x + 120, FLOOR_Y], fill=(22, 19, 28))
        d.rectangle([x, 40, x + 120, 90], fill=(34, 29, 42))
    # floor tiles
    for k in range(-1, 12):
        x = (k * 200 - scroll % 200)
        d.rectangle([x, FLOOR_Y, x + 196, 1080], fill=(28, 24, 32) if k % 2 == 0 else (24, 20, 28))
        d.line([(x, FLOOR_Y), (x, 1080)], fill=(14, 12, 18), width=4)
    d.line([(0, FLOOR_Y), (1920, FLOOR_Y)], fill=(48, 40, 54), width=6)
    # torch light pool (flicker)
    fl = 0.85 + 0.15 * (0.5 + 0.5 * math.sin(t * 23) * math.sin(t * 7.3)) + random.uniform(-0.03, 0.03)
    glow = Image.new('L', (1920, 1080), 0)
    ImageDraw.Draw(glow).ellipse([960 - 620, 120, 960 + 620, 1080], fill=int(110 * fl))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    warm = Image.new('RGB', (1920, 1080), (255, 160, 90))
    im = Image.composite(warm, im, glow.point(lambda v: int(v * 0.45)))
    # shadow
    sh = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([960 - 200, FLOOR_Y - 30, 960 + 200, FLOOR_Y + 30], fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    im = im.convert('RGBA'); im.alpha_composite(sh)
    # sprite
    spr = (idle if mode == 'idle' else walk)[fi]
    im.alpha_composite(spr, (960 - spr.width // 2, FLOOR_Y - spr.height + 3 * SC))
    # title (appears at 0.5s, sits top-left; label bottom-right during walk)
    d = ImageDraw.Draw(im)
    if t >= 0.5:
        a = min(1, (t - 0.5) / 0.3)
        d.text((80, 80), 'PIXEL KNIGHT', font=font, fill=(255, 255, 255, int(255 * a)))
        d.text((80, 170), 'SIR ZERO OF THE SCRATCHPAD', font=font_s, fill=(160, 150, 170, int(255 * a)))
    tag = {'idle': 'IDLE  6F', 'walk': 'WALK  6F'}[mode]
    d.text((1920 - 80 - 22 * len(tag), 1000), tag, font=font_s, fill=(120, 110, 130, 255))
    im.convert('RGB').save(f'{OUT}/s{i:04d}.jpg', quality=93)
    if i % 100 == 0: print(i, '/', N)
print('DONE', N)

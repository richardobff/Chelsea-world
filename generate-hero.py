#!/usr/bin/env python3
"""
Generative ASCII Art Video for Chelsea's World Hero Section
Theme: "Emergent Intelligence" - Flowing energy, self-organizing particles, neural patterns

Requirements:
- Resolution: 1920x400 (wide banner format)
- Duration: 10 seconds, seamlessly looping
- Colors: Cyan (#48dbfb) and pink (#ff9ff3) on dark background (#0a0a0a)
- Style: Organic but digital, subtle, mesmerizing
- Output: /Users/officebff/chelsea-dashboard/assets/hero-emergence.mp4
"""

import os
import sys
import math
import random
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ProcessPoolExecutor, as_completed

# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_PATH = "/Users/officebff/chelsea-dashboard/assets/hero-emergence.mp4"
DURATION = 10.0  # seconds
FPS = 24
VW, VH = 1920, 400  # wide banner format

# Color palette
BG_COLOR = (10, 10, 10)  # #0a0a0a
CYAN = np.array([0x48, 0xdb, 0xfb], dtype=np.float32)
PINK = np.array([0xff, 0x9f, 0xf3], dtype=np.float32)

# Grid settings
FONT_SIZE = 12
GRID_DENSITY = "md"

# Particle system
N_PARTICLES = 400
PARTICLE_LIFETIME = 3.0
FLOW_SCALE = 0.008
FLOW_SPEED = 0.3

# =============================================================================
# CHARACTER PALETTES
# =============================================================================

# Neural/network themed characters
PAL_NEURAL = list("·∘○◌◯●◉◎◐◑◒◓◔◕◖◗")  # circles for nodes
PAL_CONNECTIONS = list("╱╲│─┌┐└┘├┤┬┴┼═║╔╗╚╝")  # connection lines
PAL_DATA = list("01x∿~≈≋∞∑∫∂∆∇")  # data/flow symbols
PAL_GLOW = list(" .·•●█")  # glow intensity

ALL_CHARS = set()
for pal in [PAL_NEURAL, PAL_CONNECTIONS, PAL_DATA, PAL_GLOW]:
    ALL_CHARS.update(pal)
ALL_CHARS.discard(" ")

# =============================================================================
# FONT DETECTION
# =============================================================================

def find_font():
    """Find a suitable monospace font."""
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/Windows/Fonts/consola.ttf",
        "/Windows/Fonts/cour.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("No monospace font found")

FONT_PATH = find_font()

# =============================================================================
# GRID LAYER
# =============================================================================

class GridLayer:
    """ASCII character grid with precomputed coordinate arrays."""
    
    def __init__(self, font_path, font_size, vw=VW, vh=VH):
        self.vw = vw
        self.vh = vh
        
        self.font = ImageFont.truetype(font_path, font_size)
        asc, desc = self.font.getmetrics()
        bbox = self.font.getbbox("M")
        self.cw = bbox[2] - bbox[0]
        self.ch = asc + desc
        
        self.cols = vw // self.cw
        self.rows = vh // self.ch
        self.ox = (vw - self.cols * self.cw) // 2
        self.oy = (vh - self.rows * self.ch) // 2
        
        # Coordinate arrays
        self.rr = np.arange(self.rows, dtype=np.float32)[:, None]
        self.cc = np.arange(self.cols, dtype=np.float32)[None, :]
        
        # Normalized center-based coords
        cx, cy = self.cols / 2.0, self.rows / 2.0
        self.dx = (self.cc - cx) / max(self.cols, 1)
        self.dy = (self.rr - cy) / max(self.rows, 1)
        self.dist = np.sqrt(self.dx**2 + self.dy**2)
        self.angle = np.arctan2(self.dy, self.dx)
        
        # Pre-rasterize characters
        self.bm = {}
        for c in ALL_CHARS:
            img = Image.new("L", (self.cw, self.ch), 0)
            ImageDraw.Draw(img).text((0, 0), c, fill=255, font=self.font)
            self.bm[c] = np.array(img, dtype=np.float32) / 255.0
    
    def render(self, chars, colors, canvas=None):
        """Render characters to pixel canvas."""
        if canvas is None:
            canvas = np.zeros((self.vh, self.vw, 3), dtype=np.uint8)
        
        for row in range(self.rows):
            y = self.oy + row * self.ch
            if y + self.ch > self.vh:
                break
            for col in range(self.cols):
                c = chars[row, col]
                if c == " ":
                    continue
                x = self.ox + col * self.cw
                if x + self.cw > self.vw:
                    break
                
                alpha = self.bm.get(c)
                if alpha is not None:
                    color = colors[row, col]
                    blended = (alpha[:, :, None] * color).astype(np.uint8)
                    canvas[y:y+self.ch, x:x+self.cw] = np.maximum(
                        canvas[y:y+self.ch, x:x+self.cw], blended
                    )
        return canvas


# =============================================================================
# FLOW FIELD & PARTICLE SYSTEM
# =============================================================================

def flow_field(g, t, scale=FLOW_SCALE, speed=FLOW_SPEED):
    """
    Generate a flowing vector field based on multiple sine waves.
    Creates organic, neural-like patterns.
    """
    # Layered sine waves for organic flow
    f1 = np.sin(g.cc * scale * 2 + t * speed * 3)
    f2 = np.cos(g.rr * scale * 1.5 + t * speed * 2)
    f3 = np.sin((g.cc + g.rr) * scale * 1.2 - t * speed * 1.5)
    f4 = np.cos(np.sqrt(g.cc**2 + g.rr**2) * scale * 0.8 + t * speed * 2.5)
    
    # Combine for vector field angles
    angle_field = (f1 * 0.3 + f2 * 0.25 + f3 * 0.25 + f4 * 0.2) * np.pi
    
    # Add vortex swirl from center
    swirl = g.angle + g.dist * 0.5 * np.sin(t * 0.5)
    angle_field = angle_field * 0.7 + swirl * 0.3
    
    return np.cos(angle_field), np.sin(angle_field)


class ParticleSystem:
    """Self-organizing particles following flow field."""
    
    def __init__(self, grid, n_particles=N_PARTICLES):
        self.g = grid
        self.n = n_particles
        self.px = np.random.uniform(0, grid.cols, n_particles).astype(np.float32)
        self.py = np.random.uniform(0, grid.rows, n_particles).astype(np.float32)
        self.vx = np.zeros(n_particles, dtype=np.float32)
        self.vy = np.zeros(n_particles, dtype=np.float32)
        self.life = np.random.uniform(0, 1, n_particles).astype(np.float32)
        self.age = np.random.uniform(0, PARTICLE_LIFETIME, n_particles).astype(np.float32)
        self.size = np.random.uniform(0.5, 2.0, n_particles).astype(np.float32)
        
    def update(self, t, dt):
        """Update particle positions following flow field."""
        # Get flow vectors at particle positions
        vx_field, vy_field = flow_field(self.g, t)
        
        # Sample flow at particle positions (bilinear interpolation)
        px_int = np.clip(self.px.astype(int), 0, self.g.cols - 1)
        py_int = np.clip(self.py.astype(int), 0, self.g.rows - 1)
        
        flow_x = vx_field[py_int, px_int]
        flow_y = vy_field[py_int, px_int]
        
        # Add attraction to center for emergent clustering
        cx, cy = self.g.cols / 2, self.g.rows / 2
        to_cx = (cx - self.px) / max(self.g.cols, 1)
        to_cy = (cy - self.py) / max(self.g.rows, 1)
        
        # Combine flow with center attraction (weak, for organic feel)
        attraction_strength = 0.02 * (1 + 0.5 * np.sin(t * 0.7))
        self.vx += (flow_x * 0.15 + to_cx * attraction_strength) * dt * 60
        self.vy += (flow_y * 0.15 + to_cy * attraction_strength) * dt * 60
        
        # Damping
        self.vx *= 0.95
        self.vy *= 0.95
        
        # Update positions
        self.px += self.vx
        self.py += self.vy
        
        # Age particles
        self.age += dt
        self.life = 1 - np.clip(self.age / PARTICLE_LIFETIME, 0, 1)
        
        # Respawn dead particles
        dead = self.life <= 0.01
        n_dead = np.sum(dead)
        if n_dead > 0:
            # Respawn with preference for edges and center
            theta = np.random.uniform(0, 2 * np.pi, n_dead)
            r = np.random.choice([
                np.random.uniform(0, 0.2, n_dead),
                np.random.uniform(0.8, 1.0, n_dead)
            ]).flatten()[:n_dead]
            
            self.px[dead] = self.g.cols * (0.5 + r * np.cos(theta) * 0.5)
            self.py[dead] = self.g.rows * (0.5 + r * np.sin(theta) * 0.5)
            self.vx[dead] = 0
            self.vy[dead] = 0
            self.age[dead] = 0
            self.life[dead] = 1.0
    
    def render(self, t):
        """Render particles to grid."""
        chars = np.full((self.g.rows, self.g.cols), " ", dtype="U1")
        colors = np.zeros((self.g.rows, self.g.cols, 3), dtype=np.float32)
        
        # Particle type based on life phase
        for i in range(self.n):
            if self.life[i] < 0.01:
                continue
                
            px, py = int(self.px[i]), int(self.py[i])
            if not (0 <= px < self.g.cols and 0 <= py < self.g.rows):
                continue
            
            # Choose character based on life and velocity
            speed = np.sqrt(self.vx[i]**2 + self.vy[i]**2)
            char_idx = int(speed * 2) % len(PAL_NEURAL)
            chars[py, px] = PAL_NEURAL[char_idx]
            
            # Color gradient: cyan (young) → pink (old) with time-based shift
            color_t = (self.life[i] * 0.7 + np.sin(t * 0.5 + i * 0.1) * 0.3 + 1) / 2
            color_t = np.clip(color_t, 0, 1)
            
            # Blend between cyan and pink
            color = CYAN * (1 - color_t) + PINK * color_t
            
            # Add glow based on life
            intensity = self.life[i] ** 0.5 * 255
            colors[py, px] = color * intensity / 255.0
            
            # Add trail effect for fast particles
            if speed > 0.5 and self.life[i] > 0.3:
                trail_len = min(3, int(speed * 2))
                for j in range(1, trail_len + 1):
                    tx = int(px - self.vx[i] * j * 0.5)
                    ty = int(py - self.vy[i] * j * 0.5)
                    if 0 <= tx < self.g.cols and 0 <= ty < self.g.rows:
                        if chars[ty, tx] == " ":
                            chars[ty, tx] = PAL_DATA[j % len(PAL_DATA)]
                            trail_intensity = intensity * (1 - j / (trail_len + 1)) * 0.5
                            colors[ty, tx] = color * trail_intensity / 255.0
        
        return chars, colors


# =============================================================================
# NEURAL NETWORK VISUALIZATION
# =============================================================================

def render_neural_field(g, t):
    """
    Render a field representing neural activations.
    Creates pulsing node patterns with connecting energy.
    """
    # Create a grid of "neuron" activation values
    node_spacing = max(g.cols, g.rows) / 6
    
    val = np.zeros((g.rows, g.cols), dtype=np.float32)
    
    # Place virtual neurons
    n_nodes = 12
    rng = np.random.RandomState(42)  # deterministic
    
    for i in range(n_nodes):
        nx = (0.2 + 0.6 * rng.random()) * g.cols
        ny = (0.2 + 0.6 * rng.random()) * g.rows
        
        # Pulsing activation
        pulse = 0.5 + 0.5 * np.sin(t * 2 + i * 0.8)
        
        # Distance from this node
        dx = g.cc - nx
        dy = g.rr - ny
        dist = np.sqrt(dx**2 + dy**2)
        
        # Gaussian activation field
        activation = np.exp(-dist**2 / (2 * (node_spacing * 0.4)**2)) * pulse
        val += activation
    
    # Add connecting energy between nearby nodes (simplified)
    connection_wave = np.sin(g.cc * 0.1 + t) * np.cos(g.rr * 0.08 - t * 0.7)
    val = val * 0.7 + connection_wave * 0.15
    
    return np.clip(val, 0, 1)


def render_energy_waves(g, t):
    """Render flowing energy waves across the field."""
    waves = np.zeros((g.rows, g.cols), dtype=np.float32)
    
    # Multiple wave layers
    for i in range(3):
        freq = 0.05 + i * 0.02
        speed = 0.3 + i * 0.15
        phase = t * speed + i * 2
        
        # Diagonal waves
        wave = np.sin((g.cc + g.rr) * freq + phase)
        # Fade at edges
        fade = np.exp(-((g.dx)**2 + (g.dy)**2) * 2)
        waves += wave * fade * (0.4 - i * 0.1)
    
    return np.clip(waves * 0.5 + 0.5, 0, 1)


# =============================================================================
# COLOR UTILITIES
# =============================================================================

def mix_colors(val, t):
    """
    Map value field to colors using cyan/pink palette.
    val: 0-1 value field
    t: time for animated color shifts
    """
    # Create color shift based on position and time
    hue_shift = np.sin(val * np.pi + t * 0.5) * 0.3
    
    # Mix cyan and pink based on value and time
    color_t = (val * 0.8 + np.sin(t * 0.3) * 0.2 + 1) / 2
    color_t = np.clip(color_t, 0, 1)
    
    # Base color interpolation
    base_color = CYAN[None, None, :] * (1 - color_t[:, :, None]) + PINK[None, None, :] * color_t[:, :, None]
    
    # Add subtle variation
    variation = np.sin(val * np.pi * 2 + t)[:, :, None] * 20
    
    color = base_color + variation
    return np.clip(color, 0, 255).astype(np.uint8)


# =============================================================================
# SHADERS
# =============================================================================

def sh_bloom(canvas, threshold=100, radius=3):
    """Subtle bloom/glow effect for ethereal feel."""
    from scipy.ndimage import gaussian_filter
    
    # Extract bright areas
    bright = np.where(np.mean(canvas, axis=2) > threshold, canvas, 0)
    
    # Blur
    bloom = np.zeros_like(canvas)
    for c in range(3):
        bloom[:, :, c] = gaussian_filter(bright[:, :, c].astype(float), sigma=radius)
    
    # Additive blend with reduced intensity for subtlety
    result = canvas.astype(float) + bloom * 0.4
    return np.clip(result, 0, 255).astype(np.uint8)


def sh_vignette(canvas, strength=0.25):
    """Subtle vignette to focus attention on center."""
    h, w = canvas.shape[:2]
    y, x = np.ogrid[:h, :w]
    
    center_y, center_x = h // 2, w // 2
    dist = np.sqrt((x - center_x)**2 / (w/2)**2 + (y - center_y)**2 / (h/2)**2)
    
    vignette = np.clip(1 - dist * strength, 0.3, 1.0)
    
    return (canvas.astype(float) * vignette[:, :, None]).astype(np.uint8)


def sh_color_grade(canvas, cyan_boost=1.2, pink_tint=0.15):
    """Enhance cyan/pink tones."""
    result = canvas.astype(float)
    
    # Boost cyan channel (blue + green)
    result[:, :, 0] *= 1.0  # Red unchanged
    result[:, :, 1] *= cyan_boost  # Green boost
    result[:, :, 2] *= cyan_boost  # Blue boost
    
    # Add subtle pink tint to shadows
    shadow_mask = np.mean(result, axis=2) < 50
    result[shadow_mask] = result[shadow_mask] * (1 - pink_tint) + PINK * pink_tint
    
    return np.clip(result, 0, 255).astype(np.uint8)


# =============================================================================
# MAIN RENDERING
# =============================================================================

def render_frame(frame_idx, grid, particles, total_frames):
    """Render a single frame."""
    # Seamless loop: t goes 0 -> 1 over the duration
    t = (frame_idx / total_frames) * 2 * np.pi
    
    # Update particles
    dt = 1.0 / FPS
    particles.update(t, dt)
    
    # Start with dark background
    canvas = np.full((VH, VW, 3), BG_COLOR[0], dtype=np.uint8)
    
    # Render neural field as background layer
    neural_val = render_neural_field(grid, t)
    neural_chars = np.full((grid.rows, grid.cols), " ", dtype="U1")
    
    # Map neural values to characters
    for i, row in enumerate(neural_val):
        for j, v in enumerate(row):
            if v > 0.1:
                char_idx = int(v * (len(PAL_GLOW) - 1))
                neural_chars[i, j] = PAL_GLOW[min(char_idx, len(PAL_GLOW) - 1)]
    
    neural_colors = mix_colors(neural_val, t) * (neural_val[:, :, None] * 0.5)
    neural_colors = neural_colors.astype(np.uint8)
    
    # Render background
    canvas = grid.render(neural_chars, neural_colors, canvas)
    
    # Render energy waves
    energy_val = render_energy_waves(grid, t)
    energy_mask = energy_val > 0.4
    energy_chars = np.full((grid.rows, grid.cols), " ", dtype="U1")
    energy_chars[energy_mask] = np.random.choice(
        PAL_CONNECTIONS, size=np.sum(energy_mask)
    )
    energy_colors = mix_colors(energy_val, t + 1) * (energy_val[:, :, None] * 0.3)
    energy_colors = energy_colors.astype(np.uint8)
    
    canvas = grid.render(energy_chars, energy_colors, canvas)
    
    # Render particles
    part_chars, part_colors = particles.render(t)
    canvas = grid.render(part_chars, part_colors, canvas)
    
    # Apply shaders
    canvas = sh_bloom(canvas, threshold=80, radius=2)
    canvas = sh_vignette(canvas, strength=0.2)
    canvas = sh_color_grade(canvas)
    
    return canvas


def encode_video(frames_dir, output_path):
    """Encode frames to MP4 using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "slow",
        "-movflags", "+faststart",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}")
        return False
    return True


def main():
    print(f"Generating emergent intelligence hero video...")
    print(f"Resolution: {VW}x{VH}, Duration: {DURATION}s, FPS: {FPS}")
    
    # Initialize grid
    print("Initializing grid...")
    grid = GridLayer(FONT_PATH, FONT_SIZE)
    print(f"Grid size: {grid.cols}x{grid.rows}")
    
    # Initialize particle system
    print("Initializing particle system...")
    particles = ParticleSystem(grid, N_PARTICLES)
    
    # Calculate total frames
    total_frames = int(DURATION * FPS)
    print(f"Rendering {total_frames} frames...")
    
    # Create temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temp directory: {tmpdir}")
        
        # Render frames
        for i in range(total_frames):
            if i % 24 == 0:
                print(f"  Frame {i}/{total_frames} ({100*i//total_frames}%)")
            
            canvas = render_frame(i, grid, particles, total_frames)
            
            # Save frame
            frame_path = os.path.join(tmpdir, f"frame_{i:05d}.png")
            Image.fromarray(canvas).save(frame_path)
        
        # Encode video
        print("Encoding video...")
        if encode_video(tmpdir, OUTPUT_PATH):
            print(f"Video saved to: {OUTPUT_PATH}")
        else:
            print("Failed to encode video")
            return 1
    
    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Chelsea's World Hero: Neural Bloom Entity
An abstract, living form that emerges from the void.
Dark, organic, bioluminescent — blending seamlessly with #0a0a0a background.
"""

import os
import sys
import math
import json
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ============================================================================
# CONFIGURATION — Dark void aesthetic matching #0a0a0a background
# ============================================================================

OUTPUT_PATH = "/Users/officebff/chelsea-dashboard/assets/entity-void.mp4"
DURATION = 12.0  # Seamless loop duration
FPS = 24
WIDTH, HEIGHT = 1080, 480  # Wide hero banner format

# Color palette — matching Chelsea's World accents, but muted for dark blend
COLORS = {
    "void": (10, 10, 10),        # #0a0a0a — matches background exactly
    "cyan": (72, 219, 251),      # #48dbfb — accent-3
    "pink": (255, 159, 243),     # #ff9ff3 — accent-4  
    "amber": (254, 202, 87),     # #feca57 — accent-2
    "coral": (255, 107, 107),    # #ff6b6b — accent-1
    "blue": (84, 160, 255),      # #54a0ff — accent-5
}

# Character palettes for different entity layers
PAL_DENSITY = " .:-=+*#%@"  # Sparse to dense
PAL_ORGANIC = " ·∘○◯●◉◎"   # Organic circles
PAL_ENERGY = " ░▒▓█"       # Block energy
PAL_SYNAPSE = " .∿≋≈~"     # Wave-like connections

# ============================================================================
# GRID SYSTEM
# ============================================================================

@dataclass
class Grid:
    rows: int
    cols: int
    cell_w: int
    cell_h: int
    
    # Pre-computed coordinate arrays (centered)
    rr: np.ndarray  # Row indices
    cc: np.ndarray  # Col indices
    
    # Center-normalized coordinates
    cx: float  # Center col
    cy: float  # Center row
    dist: np.ndarray  # Distance from center (in cells)
    dist_n: np.ndarray  # Normalized distance (0-1)
    angle: np.ndarray  # Angle from center
    
    @classmethod
    def create(cls, width: int, height: int, cell_size: int = 14):
        cols = width // cell_size
        rows = height // cell_size
        cell_w = cell_size
        cell_h = int(cell_size * 1.8)  # ASCII aspect correction
        
        # Coordinate grids
        rr = np.arange(rows).reshape(-1, 1).astype(np.float32)
        cc = np.arange(cols).reshape(1, -1).astype(np.float32)
        
        # Center
        cy, cx = rows / 2.0, cols / 2.0
        max_dist = math.sqrt(cx**2 + cy**2)
        
        # Distance and angle from center
        dy = rr - cy
        dx = cc - cx
        dist = np.sqrt(dx**2 + dy**2)
        dist_n = dist / max_dist
        angle = np.arctan2(dy, dx)  # -pi to pi
        
        return cls(rows, cols, cell_w, cell_h, rr, cc, cx, cy, dist, dist_n, angle)

# ============================================================================
# UTILITIES
# ============================================================================

def hsv2rgb(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized HSV to RGB conversion. All inputs 0-1."""
    h = h % 1.0
    hi = (h * 6).astype(np.int32)
    f = (h * 6) - hi
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    
    rgb = np.zeros(h.shape + (3,), dtype=np.float32)
    
    # Switch based on hue sector
    mask0 = hi == 0
    mask1 = hi == 1
    mask2 = hi == 2
    mask3 = hi == 3
    mask4 = hi == 4
    mask5 = hi >= 5
    
    rgb[mask0] = np.stack([v[mask0], t[mask0], p[mask0]], axis=-1)
    rgb[mask1] = np.stack([q[mask1], v[mask1], p[mask1]], axis=-1)
    rgb[mask2] = np.stack([p[mask2], v[mask2], t[mask2]], axis=-1)
    rgb[mask3] = np.stack([p[mask3], q[mask3], v[mask3]], axis=-1)
    rgb[mask4] = np.stack([t[mask4], p[mask4], v[mask4]], axis=-1)
    rgb[mask5] = np.stack([v[mask5], p[mask5], q[mask5]], axis=-1)
    
    return rgb[..., 0], rgb[..., 1], rgb[..., 2]

def val2char(val: np.ndarray, mask: np.ndarray, palette: str) -> np.ndarray:
    """Map values 0-1 to characters from palette."""
    p = np.array(list(palette))
    idx = (val * (len(p) - 1)).astype(np.int32)
    idx = np.clip(idx, 0, len(p) - 1)
    chars = p[idx]
    # Empty where mask is False
    chars = np.where(mask, chars, ' ')
    return chars

def mkc(R: np.ndarray, G: np.ndarray, B: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Make color array from RGB channels."""
    return np.stack([
        np.clip(R * 255, 0, 255).astype(np.uint8),
        np.clip(G * 255, 0, 255).astype(np.uint8),
        np.clip(B * 255, 0, 255).astype(np.uint8)
    ], axis=-1)

def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t

def smoothstep(edge0, edge1, x):
    """Smooth step function."""
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)

# ============================================================================
# FONT RENDERING
# ============================================================================

class FontCache:
    def __init__(self, size: int = 12):
        self.size = size
        # Try to find a good monospace font
        font_names = ['SF Mono', 'Menlo', 'Monaco', 'Courier New', 'Courier']
        self.font = None
        for name in font_names:
            try:
                self.font = ImageFont.truetype(name, size)
                break
            except:
                continue
        if self.font is None:
            self.font = ImageFont.load_default()
        
        # Get metrics
        ascent, descent = self.font.getmetrics()
        self.cell_h = ascent + descent
        self.cell_w = self.font.getlength('M')
        
        # Character bitmap cache
        self.cache = {}
    
    def get_bitmap(self, char: str) -> np.ndarray:
        """Get grayscale bitmap for character."""
        if char not in self.cache:
            # Create image for character
            img = Image.new('L', (int(self.cell_w) + 2, self.cell_h), 0)
            draw = ImageDraw.Draw(img)
            draw.text((0, 0), char, fill=255, font=self.font)
            self.cache[char] = np.array(img)
        return self.cache[char]

# ============================================================================
# ENTITY LAYERS
# ============================================================================

class NeuralBloom:
    """
    The main entity — an organic, pulsing neural form.
    Layers of flowing energy that breathe and evolve.
    """
    
    def __init__(self, grid: Grid):
        self.g = grid
        self.time_offset = 0.0
        
        # Entity "nodes" — control points that move and pulse
        self.n_nodes = 8
        rng = np.random.RandomState(42)  # Deterministic
        self.node_base_x = rng.uniform(-0.3, 0.3, self.n_nodes)
        self.node_base_y = rng.uniform(-0.2, 0.2, self.n_nodes)
        self.node_phase = rng.uniform(0, 2*np.pi, self.n_nodes)
        self.node_freq = rng.uniform(0.3, 0.8, self.n_nodes)
        self.node_size = rng.uniform(0.08, 0.15, self.n_nodes)
    
    def render(self, t: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Render the entity at time t.
        Returns: (char_array, color_array) both shape (rows, cols, ...)
        """
        g = self.g
        
        # === CORE PULSE ===
        # Breathing rhythm — slow in/out
        breath = 0.5 + 0.5 * math.sin(t * 0.5)
        heartbeat = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 2.3)) ** 8  # Sharp pulses
        
        # === BACKGROUND FIELD ===
        # Very subtle void texture — almost black
        void_val = np.zeros((g.rows, g.cols), dtype=np.float32)
        void_val += np.sin(g.cc * 0.03 + t * 0.1) * 0.02
        void_val += np.cos(g.rr * 0.04 - t * 0.08) * 0.02
        void_val = np.clip(void_val + 0.03, 0, 0.08)  # Very dim
        
        # === ENERGY CORE ===
        # Central pulsing glow
        core_radius = 0.15 + breath * 0.05
        core_val = np.exp(-g.dist_n / core_radius) * (0.3 + heartbeat * 0.4)
        core_val *= (0.8 + 0.2 * np.sin(g.angle * 3 + t))
        
        # Core color — shifts between cyan and pink
        core_hue = 0.5 + 0.15 * math.sin(t * 0.3)  # Cyan base
        core_sat = 0.6 + 0.3 * heartbeat
        
        # === ORGANIC NODES ===
        # Moving blob-like structures
        node_val = np.zeros((g.rows, g.cols), dtype=np.float32)
        node_hue = np.full((g.rows, g.cols), 0.5, dtype=np.float32)
        
        for i in range(self.n_nodes):
            # Node position moves in organic path
            nx = self.node_base_x[i] + 0.1 * math.sin(t * self.node_freq[i] + self.node_phase[i])
            ny = self.node_base_y[i] + 0.08 * math.cos(t * self.node_freq[i] * 0.7 + self.node_phase[i])
            
            # Convert to grid coords
            ncol = g.cx + nx * g.cols * 0.5
            nrow = g.cy + ny * g.rows * 0.5
            
            # Distance from this node
            ndist = np.sqrt((g.cc - ncol)**2 + (g.rr - nrow)**2)
            ndist_n = ndist / (g.cols * self.node_size[i])
            
            # Soft blob shape
            blob = np.exp(-ndist_n ** 1.5) * (0.2 + 0.3 * breath)
            
            # Different hue per node
            hue = (0.5 + i * 0.08 + t * 0.02) % 1.0
            
            # Accumulate
            node_val = np.maximum(node_val, blob)
            node_hue = np.where(blob > 0.1, hue, node_hue)
        
        # === SYNAPTIC CONNECTIONS ===
        # Faint lines connecting energy
        synapse_val = np.zeros((g.rows, g.cols), dtype=np.float32)
        
        # Radial waves emanating from center
        for ring_i in range(4):
            ring_r = 0.15 + ring_i * 0.12 + 0.05 * math.sin(t * 0.4 + ring_i)
            ring_w = 0.02 + 0.01 * breath
            ring_d = np.abs(g.dist_n - ring_r)
            ring = np.clip(1 - ring_d / ring_w, 0, 1) * 0.15 * (1 - g.dist_n * 0.5)
            synapse_val = np.maximum(synapse_val, ring)
        
        # Spiral arms
        for arm_i in range(3):
            arm_offset = arm_i * (2 * math.pi / 3)
            spiral = g.angle + arm_offset - g.dist_n * 4 + t * 0.3
            arm_val = np.clip(np.cos(spiral * 2) * 0.5 + 0.5, 0, 1)
            arm_val *= np.exp(-g.dist_n * 1.5) * 0.1
            synapse_val = np.maximum(synapse_val, arm_val)
        
        # === COMPOSITE ===
        # Layer everything
        
        # Start with void
        final_val = void_val
        final_hue = np.full((g.rows, g.cols), 0.55, dtype=np.float32)  # Blue-void
        final_sat = np.full((g.rows, g.cols), 0.2, dtype=np.float32)
        
        # Add synaptic connections (faint cyan)
        mask = synapse_val > 0.01
        final_val = np.where(mask, np.maximum(final_val, synapse_val), final_val)
        final_hue = np.where(mask, 0.5, final_hue)  # Cyan
        final_sat = np.where(mask, 0.4, final_sat)
        
        # Add organic nodes
        mask = node_val > 0.05
        final_val = np.where(mask, np.maximum(final_val, node_val), final_val)
        final_hue = np.where(mask, node_hue, final_hue)
        final_sat = np.where(mask, 0.6, final_sat)
        
        # Add energy core (brightest, on top)
        mask = core_val > 0.02
        blend = core_val * 0.8
        final_val = np.where(mask, np.maximum(final_val, blend), final_val)
        final_hue = np.where(mask, core_hue, final_hue)
        final_sat = np.where(mask, core_sat, final_sat)
        
        # === COLOR CONVERSION ===
        R, G, B = hsv2rgb(final_hue, final_sat, final_val)
        colors = mkc(R, G, B, g.rows, g.cols)
        
        # === CHARACTER SELECTION ===
        # Map values to characters
        char_mask = final_val > 0.03
        chars = val2char(final_val, char_mask, PAL_DENSITY)
        
        return chars, colors

# ============================================================================
# RENDERER
# ============================================================================

class Renderer:
    def __init__(self, width: int, height: int, grid: Grid):
        self.w = width
        self.h = height
        self.g = grid
        self.font = FontCache(size=12)
        
        # Create entity
        self.entity = NeuralBloom(grid)
    
    def render_frame(self, t: float) -> np.ndarray:
        """Render a single frame at time t. Returns RGB uint8 array."""
        
        # Get entity layer
        chars, colors = self.entity.render(t)
        
        # Create output canvas (start with void color)
        canvas = np.full((self.h, self.w, 3), 10, dtype=np.uint8)  # #0a0a0a
        
        # Render characters
        for row in range(self.g.rows):
            for col in range(self.g.cols):
                char = chars[row, col]
                if char == ' ':
                    continue
                
                color = colors[row, col]
                
                # Get bitmap for character
                bitmap = self.font.get_bitmap(char)
                bh, bw = bitmap.shape
                
                # Calculate position
                x = int(col * self.font.cell_w)
                y = int(row * self.font.cell_h * 0.55)  # Adjust for visual spacing
                
                # Clip to canvas bounds
                x2 = min(x + bw, self.w)
                y2 = min(y + bh, self.h)
                bw_clip = x2 - x
                bh_clip = y2 - y
                
                if bw_clip <= 0 or bh_clip <= 0:
                    continue
                
                # Composite with alpha from bitmap
                bitmap_crop = bitmap[:bh_clip, :bw_clip]
                alpha = bitmap_crop.astype(np.float32) / 255.0
                
                # Blend
                for c in range(3):
                    dest = canvas[y:y2, x:x2, c].astype(np.float32)
                    src = color[c] * alpha
                    canvas[y:y2, x:x2, c] = (dest * (1 - alpha) + src).astype(np.uint8)
        
        return canvas

# ============================================================================
# ENCODING
# ============================================================================

def encode_video(frames: List[np.ndarray], output_path: str, fps: int):
    """Encode frames to H.264 MP4 using ffmpeg."""
    
    if not frames:
        raise ValueError("No frames to encode")
    
    h, w = frames[0].shape[:2]
    
    # FFmpeg command
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{w}x{h}',
        '-pix_fmt', 'rgb24',
        '-r', str(fps),
        '-i', '-',  # Read from stdin
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',  # High quality
        '-preset', 'medium',
        '-movflags', '+faststart',
        '-vf', 'format=yuv420p',
        output_path
    ]
    
    # Start ffmpeg
    stderr_path = output_path + '.stderr'
    with open(stderr_path, 'w') as stderr_fh:
        pipe = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=stderr_fh
        )
        
        try:
            for frame in frames:
                pipe.stdin.write(frame.tobytes())
            pipe.stdin.close()
            pipe.wait()
        except Exception as e:
            pipe.kill()
            raise e
    
    # Check result
    if pipe.returncode != 0:
        with open(stderr_path) as f:
            err = f.read()
        raise RuntimeError(f"ffmpeg failed: {err}")
    
    os.remove(stderr_path)
    print(f"✓ Video encoded: {output_path}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("CHELSEA'S WORLD — Neural Bloom Entity")
    print("=" * 60)
    
    # Create grid
    print("Creating grid...")
    grid = Grid.create(WIDTH, HEIGHT, cell_size=10)
    print(f"  Grid: {grid.rows} rows × {grid.cols} cols")
    
    # Create renderer
    print("Initializing entity...")
    renderer = Renderer(WIDTH, HEIGHT, grid)
    
    # Generate frames
    n_frames = int(DURATION * FPS)
    print(f"Rendering {n_frames} frames at {FPS}fps...")
    
    frames = []
    start_time = time.time()
    
    for i in range(n_frames):
        t = (i / n_frames) * DURATION  # Seamless loop
        frame = renderer.render_frame(t)
        frames.append(frame)
        
        if (i + 1) % 24 == 0:
            elapsed = time.time() - start_time
            fps_render = (i + 1) / elapsed
            eta = (n_frames - i - 1) / fps_render
            print(f"  Frame {i+1}/{n_frames} ({fps_render:.1f} fps, ETA: {eta:.0f}s)")
    
    render_time = time.time() - start_time
    print(f"✓ Rendered {n_frames} frames in {render_time:.1f}s")
    
    # Encode
    print("Encoding video...")
    encode_video(frames, OUTPUT_PATH, FPS)
    
    print("=" * 60)
    print("DONE")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()

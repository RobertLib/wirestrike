import pygame
import math
import random
import sys
from typing import List, Tuple, Optional, Union

# --- CONSTANTS ---
WIDTH: int = 800
HEIGHT: int = 600
FPS: int = 60
FOV: float = 400.0  # Field of View

# Colors
BLACK: Tuple[int, int, int] = (0, 0, 0)
GREEN: Tuple[int, int, int] = (0, 255, 0)
DARK_GREEN: Tuple[int, int, int] = (0, 100, 0)
CYAN: Tuple[int, int, int] = (0, 255, 255)
RED: Tuple[int, int, int] = (255, 50, 50)
YELLOW: Tuple[int, int, int] = (255, 255, 0)
WHITE: Tuple[int, int, int] = (255, 255, 255)


# --- 3D ENGINE ---
def project(x: float, y: float, z: float) -> Optional[Tuple[int, int]]:
    """Converts 3D coordinates to 2D screen coordinates."""
    if z < 0.1:  # Prevent division by zero and rendering behind camera
        return None
    factor: float = FOV / z
    px: float = WIDTH / 2 + x * factor
    py: float = HEIGHT / 2 - y * factor  # Pygame Y axis is inverted
    return int(px), int(py)


def draw_wireframe(
    surface: pygame.Surface,
    color: Tuple[int, int, int],
    cx: float,
    cy: float,
    cz: float,
    verts: List[Tuple[float, float, float]],
    edges: List[Tuple[int, int]],
    scale: float = 1.0,
    angle_z: float = 0.0,
) -> None:
    """Draws a 3D wireframe model."""
    projected: List[Optional[Tuple[int, int]]] = []
    for v in verts:
        # Rotation around Z axis (for ship banking)
        rx: float = v[0] * math.cos(angle_z) - v[1] * math.sin(angle_z)
        ry: float = v[0] * math.sin(angle_z) + v[1] * math.cos(angle_z)
        rz: float = v[2]

        # Translation and scaling
        wx: float = cx + rx * scale
        wy: float = cy + ry * scale
        wz: float = cz + rz * scale

        projected.append(project(wx, wy, wz))

    for e in edges:
        p1: Optional[Tuple[int, int]] = projected[e[0]]
        p2: Optional[Tuple[int, int]] = projected[e[1]]
        if p1 and p2:
            pygame.draw.line(surface, color, p1, p2, 2)


# --- MODELS (Vertices and edges) ---
# Player ship (Arwing style)
PLAYER_VERTS: List[Tuple[float, float, float]] = [
    (0, 0, 2),  # 0: Nose
    (-2, -0.5, -1),  # 1: Left wing
    (2, -0.5, -1),  # 2: Right wing
    (0, 1, -1),  # 3: Top fin
    (0, -0.5, -1),  # 4: Engine bottom
]
PLAYER_EDGES: List[Tuple[int, int]] = [
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 3),
    (2, 3),
    (1, 4),
    (2, 4),
    (3, 4),
]

# Enemy (Octahedron / Diamond)
ENEMY_VERTS: List[Tuple[float, float, float]] = [
    (0, 1, 0),
    (1, 0, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]
ENEMY_EDGES: List[Tuple[int, int]] = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),  # Center square
    (4, 0),
    (4, 1),
    (4, 2),
    (4, 3),  # Front pyramid
    (5, 0),
    (5, 1),
    (5, 2),
    (5, 3),  # Back pyramid
]

# Obstacle (Cube)
OBSTACLE_VERTS: List[Tuple[float, float, float]] = [
    (-1, -1, -1),
    (1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (-1, -1, 1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, 1, 1),
]
OBSTACLE_EDGES: List[Tuple[int, int]] = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 4),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
]


# --- GAME CLASSES ---
class Player:
    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 10.0  # Fixed distance from camera
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.speed: float = 15.0
        self.bank_angle: float = 0.0
        self.cooldown: float = 0.0
        self.hp: int = 100

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        # Movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.speed
        else:
            self.vx *= 0.8  # Friction

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.vy = self.speed
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.vy = -self.speed
        else:
            self.vy *= 0.8

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Screen boundaries
        self.x = max(-15.0, min(15.0, self.x))
        self.y = max(-8.0, min(8.0, self.y))

        # Ship banking based on horizontal movement
        target_bank: float = -self.vx * 0.05
        self.bank_angle += (target_bank - self.bank_angle) * 10 * dt

        if self.cooldown > 0:
            self.cooldown -= dt

    def draw(self, surface: pygame.Surface) -> None:
        draw_wireframe(
            surface,
            CYAN,
            self.x,
            self.y,
            self.z,
            PLAYER_VERTS,
            PLAYER_EDGES,
            scale=0.8,
            angle_z=self.bank_angle,
        )


class Laser:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.speed: float = 100.0
        self.active: bool = True

    def update(self, dt: float) -> None:
        self.z += self.speed * dt
        if self.z > 150:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        p1: Optional[Tuple[int, int]] = project(self.x, self.y, self.z)
        p2: Optional[Tuple[int, int]] = project(self.x, self.y, self.z + 2)
        if p1 and p2:
            pygame.draw.line(surface, YELLOW, p1, p2, 3)


class Enemy:
    def __init__(self) -> None:
        self.x: float = random.uniform(-15, 15)
        self.y: float = random.uniform(-5, 10)
        self.z: float = 150.0
        self.speed: float = random.uniform(20, 40)
        self.active: bool = True
        self.radius: float = 1.5

    def update(self, dt: float) -> None:
        self.z -= self.speed * dt
        if self.z < 0:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        draw_wireframe(
            surface,
            RED,
            self.x,
            self.y,
            self.z,
            ENEMY_VERTS,
            ENEMY_EDGES,
            scale=1.5,
            angle_z=pygame.time.get_ticks() * 0.005,
        )


class Obstacle:
    def __init__(self) -> None:
        self.x: float = random.uniform(-20, 20)
        self.y: float = -8.0  # On the ground
        self.z: float = 150.0
        self.speed: float = 30.0  # Environment scrolling speed
        self.active: bool = True
        self.radius: float = 2.0

    def update(self, dt: float) -> None:
        self.z -= self.speed * dt
        if self.z < 0:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        draw_wireframe(
            surface,
            GREEN,
            self.x,
            self.y,
            self.z,
            OBSTACLE_VERTS,
            OBSTACLE_EDGES,
            scale=2.0,
        )


class Particle:
    def __init__(
        self, x: float, y: float, z: float, color: Tuple[int, int, int]
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.vx: float = random.uniform(-10, 10)
        self.vy: float = random.uniform(-10, 10)
        self.vz: float = random.uniform(-10, 10)
        self.life: float = 1.0
        self.color: Tuple[int, int, int] = color

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.life -= dt

    def draw(self, surface: pygame.Surface) -> None:
        p: Optional[Tuple[int, int]] = project(self.x, self.y, self.z)
        if p:
            pygame.draw.circle(surface, self.color, p, max(1, int(3 * self.life)))


# --- MAIN GAME ---
def main() -> None:
    pygame.init()
    screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PyFox: Vector Shooter")
    clock: pygame.time.Clock = pygame.time.Clock()
    font: pygame.font.Font = pygame.font.SysFont(None, 36)

    player: Player = Player()
    lasers: List[Laser] = []
    enemies: List[Enemy] = []
    obstacles: List[Obstacle] = []
    particles: List[Particle] = []

    score: int = 0
    world_speed: float = 30.0
    scroll_offset: float = 0.0

    running: bool = True
    game_over: bool = False

    while running:
        dt: float = clock.tick(FPS) / 1000.0

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    if player.cooldown <= 0:
                        lasers.append(Laser(player.x - 1.5, player.y, player.z))
                        lasers.append(Laser(player.x + 1.5, player.y, player.z))
                        player.cooldown = 0.2
                if event.key == pygame.K_r and game_over:
                    # Restart
                    player = Player()
                    lasers.clear()
                    enemies.clear()
                    obstacles.clear()
                    particles.clear()
                    score = 0
                    game_over = False

        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()

        if not game_over:
            # --- UPDATE ---
            player.update(dt, keys)

            # Grid scrolling
            scroll_offset += world_speed * dt
            if scroll_offset > 10:
                scroll_offset -= 10

            # Generate enemies and obstacles
            if random.random() < 0.02:
                enemies.append(Enemy())
            if random.random() < 0.03:
                obstacles.append(Obstacle())

            # Update entities
            for l in lasers:
                l.update(dt)
            for e in enemies:
                e.update(dt)
            for o in obstacles:
                o.update(dt)
            for p in particles:
                p.update(dt)

            # Remove inactive
            lasers = [l for l in lasers if l.active]
            enemies = [e for e in enemies if e.active]
            obstacles = [o for o in obstacles if o.active]
            particles = [p for p in particles if p.life > 0]

            # Collisions: Lasers vs Enemies
            for l in lasers:
                for e in enemies:
                    if not e.active or not l.active:
                        continue
                    dist: float = math.sqrt(
                        (l.x - e.x) ** 2 + (l.y - e.y) ** 2 + (l.z - e.z) ** 2
                    )
                    if dist < e.radius + 1.0:
                        e.active = False
                        l.active = False
                        score += 100
                        # Explosion
                        for _ in range(15):
                            particles.append(Particle(e.x, e.y, e.z, RED))
                        for _ in range(10):
                            particles.append(Particle(e.x, e.y, e.z, YELLOW))

            # Collisions: Player vs Enemies/Obstacles
            for entity in enemies + obstacles:  # type: ignore
                if not entity.active:
                    continue
                dist: float = math.sqrt(
                    (player.x - entity.x) ** 2
                    + (player.y - entity.y) ** 2
                    + (player.z - entity.z) ** 2
                )
                if dist < entity.radius + 1.5:
                    entity.active = False
                    player.hp -= 25
                    for _ in range(20):
                        particles.append(Particle(player.x, player.y, player.z, CYAN))
                    if player.hp <= 0:
                        game_over = True

        # --- DRAWING ---
        screen.fill(BLACK)

        # Draw ground (grid)
        floor_y: float = -10.0
        # Horizontal lines
        for i in range(15):
            z: float = 150 - (scroll_offset + i * 10)
            if z > 0.1:
                p1: Optional[Tuple[int, int]] = project(-50, floor_y, z)
                p2: Optional[Tuple[int, int]] = project(50, floor_y, z)
                if p1 and p2:
                    pygame.draw.line(screen, DARK_GREEN, p1, p2, 1)
        # Depth lines
        for x in range(-50, 51, 10):
            p1: Optional[Tuple[int, int]] = project(x, floor_y, 0.1)
            p2: Optional[Tuple[int, int]] = project(x, floor_y, 150)
            if p1 and p2:
                pygame.draw.line(screen, DARK_GREEN, p1, p2, 1)

        # Draw entities (sorted by Z for correct overlapping, though not strictly necessary for wireframe)
        all_entities: List[Union[Enemy, Obstacle, Particle, Laser]] = []
        all_entities.extend(enemies)
        all_entities.extend(obstacles)
        all_entities.extend(particles)
        all_entities.extend(lasers)
        all_entities.sort(key=lambda e: e.z, reverse=True)

        for e in all_entities:
            e.draw(screen)

        if not game_over:
            player.draw(screen)

        # UI
        score_text: pygame.Surface = font.render(f"SCORE: {score}", True, WHITE)
        hp_text: pygame.Surface = font.render(
            f"HP: {player.hp}", True, RED if player.hp <= 25 else GREEN
        )
        screen.blit(score_text, (10, 10))
        screen.blit(hp_text, (10, 40))

        if game_over:
            go_text: pygame.Surface = font.render(
                "GAME OVER - Press R to restart", True, RED
            )
            screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

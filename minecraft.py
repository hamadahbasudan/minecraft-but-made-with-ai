import math
import random
import tkinter as tk

WIDTH = 960
HEIGHT = 540
BLOCK = 32

COLORS = {
    "sky": "#9ad7ff",
    "grass": "#5fbf5f",
    "dirt": "#8b5a2b",
    "stone": "#8a8d8f",
    "wood": "#8b5a2b",
    "leaf": "#3c9f4a",
    "sun": "#ffd166",
    "cloud": "#f5f7ff",
    "player": "#ffca3a",
    "outline": "#333333",
    "ui": "#1b1b1b",
    "ui_alt": "#2f2f2f",
    "selected": "#ffd166",
}


class MiniMinecraft:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Minecraft")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=COLORS["sky"], highlightthickness=0)
        self.canvas.pack()

        self.world = {}
        self.generate_world()

        self.player = {
            "x": 100.0,
            "y": 120.0,
            "w": 28,
            "h": 48,
            "vx": 0.0,
            "vy": 0.0,
            "on_ground": False,
        }

        self.keys = set()
        self.camera_x = 0
        self.selected = "grass"
        self.inventory = {"grass": 20, "dirt": 30, "stone": 20, "wood": 10, "leaf": 10}

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.break_block)
        self.canvas.bind("<Button-3>", self.place_block)
        self.root.focus_set()

        self.root.after(16, self.game_loop)

    def on_key_press(self, event):
        key = event.keysym.lower()

        if key in {"1", "2", "3", "4", "5"}:
            slots = ["grass", "dirt", "stone", "wood", "leaf"]
            self.selected = slots[int(key) - 1]
            return

        if key in {"a", "left"}:
            self.keys.add("left")
        elif key in {"d", "right"}:
            self.keys.add("right")
        elif key in {"w", "up", "space"}:
            self.jump()
        elif key == "e":
            self.cycle_block()

    def on_key_release(self, event):
        key = event.keysym.lower()
        if key in {"a", "left"}:
            self.keys.discard("left")
        elif key in {"d", "right"}:
            self.keys.discard("right")

    def cycle_block(self):
        order = ["grass", "dirt", "stone", "wood", "leaf"]
        idx = order.index(self.selected)
        self.selected = order[(idx + 1) % len(order)]

    def jump(self):
        if self.player["on_ground"]:
            self.player["vy"] = -12
            self.player["on_ground"] = False

    def generate_world(self):
        for x in range(0, 220):
            # smooth terrain
            surface = 10 + int(3 * math.sin(x / 6.0) + 2 * math.sin(x / 2.6 + 1.5))
            surface = max(10, min(18, surface))

            for y in range(0, surface + 10):
                if y < surface:
                    block = "stone" if y > surface - 2 else "dirt"
                    self.world[(x, y)] = block
                elif y == surface:
                    self.world[(x, y)] = "grass"

            if random.random() < 0.12:
                tree_h = random.randint(3, 5)
                for i in range(tree_h):
                    self.world[(x, surface - i - 1)] = "wood"
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        if random.random() < 0.7:
                            self.world[(x + dx, surface - tree_h + dy)] = "leaf"

    def screen_to_tile(self, sx, sy):
        tx = int((sx + self.camera_x) // BLOCK)
        ty = int(sy // BLOCK)
        return tx, ty

    def player_rect(self):
        return {
            "x": self.player["x"],
            "y": self.player["y"],
            "w": self.player["w"],
            "h": self.player["h"],
        }

    def rect_intersects_block(self, rect, tx, ty):
        bx1 = tx * BLOCK
        by1 = ty * BLOCK
        bx2 = bx1 + BLOCK
        by2 = by1 + BLOCK

        return not (
            rect["x"] + rect["w"] <= bx1
            or rect["x"] >= bx2
            or rect["y"] + rect["h"] <= by1
            or rect["y"] >= by2
        )

    def resolve_horizontal(self):
        rect = self.player_rect()
        x_min = max(0, int(rect["x"] / BLOCK) - 1)
        x_max = min(250, int((rect["x"] + rect["w"]) / BLOCK) + 2)
        y_min = max(0, int(rect["y"] / BLOCK) - 1)
        y_max = min(60, int((rect["y"] + rect["h"]) / BLOCK) + 2)

        for tx in range(x_min, x_max):
            for ty in range(y_min, y_max):
                if (tx, ty) in self.world and self.rect_intersects_block(rect, tx, ty):
                    if self.player["vx"] > 0:
                        self.player["x"] = tx * BLOCK - self.player["w"]
                    elif self.player["vx"] < 0:
                        self.player["x"] = (tx + 1) * BLOCK
                    self.player["vx"] = 0
                    return

    def resolve_vertical(self):
        rect = self.player_rect()
        x_min = max(0, int(rect["x"] / BLOCK) - 1)
        x_max = min(250, int((rect["x"] + rect["w"]) / BLOCK) + 2)
        y_min = max(0, int(rect["y"] / BLOCK) - 1)
        y_max = min(60, int((rect["y"] + rect["h"]) / BLOCK) + 2)

        self.player["on_ground"] = False

        for tx in range(x_min, x_max):
            for ty in range(y_min, y_max):
                if (tx, ty) in self.world and self.rect_intersects_block(rect, tx, ty):
                    if self.player["vy"] > 0:
                        self.player["y"] = ty * BLOCK - self.player["h"]
                        self.player["vy"] = 0
                        self.player["on_ground"] = True
                    elif self.player["vy"] < 0:
                        self.player["y"] = (ty + 1) * BLOCK
                        self.player["vy"] = 0

    def break_block(self, event):
        tx, ty = self.screen_to_tile(event.x, event.y)
        if (tx, ty) in self.world:
            block = self.world[(tx, ty)]
            self.inventory[block] = self.inventory.get(block, 0) + 1
            del self.world[(tx, ty)]

    def place_block(self, event):
        tx, ty = self.screen_to_tile(event.x, event.y)
        if (tx, ty) in self.world:
            return

        if self.inventory.get(self.selected, 0) <= 0:
            return

        # don't allow placing block in player body
        px = self.player["x"]
        py = self.player["y"]
        if not (
            px + self.player["w"] <= tx * BLOCK
            or px >= (tx + 1) * BLOCK
            or py + self.player["h"] <= ty * BLOCK
            or py >= (ty + 1) * BLOCK
        ):
            return

        self.world[(tx, ty)] = self.selected
        self.inventory[self.selected] -= 1

    def game_loop(self):
        move = 0
        if "left" in self.keys:
            move -= 1
        if "right" in self.keys:
            move += 1

        self.player["vx"] = move * 5.5
        self.player["vy"] = min(self.player["vy"] + 0.7, 14)

        self.player["x"] += self.player["vx"]
        self.resolve_horizontal()

        self.player["y"] += self.player["vy"]
        self.resolve_vertical()

        # clamp to world edges
        if self.player["x"] < 0:
            self.player["x"] = 0
        if self.player["x"] > 220 * BLOCK - self.player["w"]:
            self.player["x"] = 220 * BLOCK - self.player["w"]

        self.camera_x = max(0, self.player["x"] - WIDTH / 2)

        if self.player["y"] > HEIGHT + 200:
            self.player["x"] = 100
            self.player["y"] = 80
            self.player["vx"] = 0
            self.player["vy"] = 0

        self.draw()
        self.root.after(16, self.game_loop)

    def draw_block(self, tx, ty, block):
        x1 = tx * BLOCK - self.camera_x
        y1 = ty * BLOCK
        x2 = x1 + BLOCK
        y2 = y1 + BLOCK

        fill = COLORS[block]
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=COLORS["outline"], width=1)

        if block == "grass":
            self.canvas.create_rectangle(x1, y1, x2, y1 + 8, fill="#7bdc5a", outline="")
        elif block == "leaf":
            self.canvas.create_rectangle(x1 + 6, y1 + 6, x2 - 6, y2 - 6, fill="#53c66b", outline="")

    def draw(self):
        self.canvas.delete("all")

        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=COLORS["sky"], outline="")
        self.canvas.create_oval(WIDTH - 120, 40, WIDTH - 30, 130, fill=COLORS["sun"], outline="")

        # clouds
        for cx, cy in [(120, 80), (500, 110), (730, 70)]:
            self.canvas.create_oval(cx, cy, cx + 40, cy + 30, fill=COLORS["cloud"], outline="")
            self.canvas.create_oval(cx + 25, cy - 10, cx + 65, cy + 20, fill=COLORS["cloud"], outline="")
            self.canvas.create_oval(cx + 50, cy, cx + 90, cy + 30, fill=COLORS["cloud"], outline="")

        for (tx, ty), block in sorted(self.world.items()):
            if tx * BLOCK - self.camera_x < -BLOCK or tx * BLOCK - self.camera_x > WIDTH + BLOCK:
                continue
            self.draw_block(tx, ty, block)

        # draw player
        px = self.player["x"] - self.camera_x
        py = self.player["y"]
        self.canvas.create_rectangle(px, py, px + self.player["w"], py + self.player["h"], fill=COLORS["player"], outline=COLORS["outline"], width=2)
        self.canvas.create_oval(px + 8, py + 8, px + 18, py + 18, fill="#1a1a1a", outline="")
        self.canvas.create_oval(px + 18, py + 8, px + 28, py + 18, fill="#1a1a1a", outline="")

        # HUD/inventory
        self.canvas.create_rectangle(18, HEIGHT - 60, WIDTH - 18, HEIGHT - 18, fill=COLORS["ui"], outline="", width=0)
        slots = ["grass", "dirt", "stone", "wood", "leaf"]
        for i, name in enumerate(slots):
            x1 = 28 + i * 110
            x2 = x1 + 90
            y1 = HEIGHT - 50
            y2 = HEIGHT - 24
            fill = COLORS["selected"] if name == self.selected else COLORS["ui_alt"]
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=COLORS["outline"], width=2)
            self.canvas.create_text(x1 + 45, y1 + 13, text=name.title(), fill="white", font=("Arial", 10, "bold"))
            self.canvas.create_text(x1 + 45, y1 + 24, text=f"x{self.inventory.get(name, 0)}", fill="#dfe6ff", font=("Arial", 9, "bold"))

        self.canvas.create_text(20, 20, text="A/D or arrows to move, W/Space to jump, E to cycle block, click to break, right-click to place", anchor="nw", fill="black", font=("Arial", 10, "bold"))


root = tk.Tk()
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)
MiniMinecraft(root)
root.mainloop()

import tkinter as tk
import random
import math
from tkinter import ttk

ENV_WIDTH = 20
ENV_HEIGHT = 20
CELL_SIZE = 30
MOVING_OBJECT_COUNT = 7

# Object types
static_objects = {
    'Tree': {'color': 'darkgreen', 'key': 'T'},
    'Bench': {'color': 'sienna', 'key': 'B'},
    'Wall': {'color': 'gray', 'key': 'W'},
    'Chair': {'color': 'darkred', 'key': 'C'},
}

moving_objects = {
    'Dog': {'color': 'orange', 'key': 'D'},
    'Bike': {'color': 'blue', 'key': 'K'},
}

object_types = {**static_objects, **moving_objects}

def dijkstra(grid, start, end):
    width, height = len(grid[0]), len(grid)
    dist = [[float('inf')] * width for _ in range(height)]
    prev = [[None] * width for _ in range(height)]
    dist[start[1]][start[0]] = 0
    visited = [[False] * width for _ in range(height)]
    queue = [(0, start)]

    while queue:
        queue.sort()
        d, (x, y) = queue.pop(0)
        if visited[y][x]:
            continue
        visited[y][x] = True

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                if grid[ny][nx] in static_objects or grid[ny][nx] in moving_objects:
                    continue
                nd = d + 1
                if nd < dist[ny][nx]:
                    dist[ny][nx] = nd
                    prev[ny][nx] = (x, y)
                    queue.append((nd, (nx, ny)))

    path = []
    current = end
    while current:
        path.insert(0, current)
        current = prev[current[1]][current[0]]
    return path if path and path[0] == start else []


class SmartAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Smart Assistant Park Simulation")
        self.env = [[None for _ in range(ENV_WIDTH)] for _ in range(ENV_HEIGHT)]
        self.path_trail = []
        self.moving_objects_positions = []

        while True:
            self.user_x, self.user_y = self.get_random_empty_cell()
            self.dest_x, self.dest_y = self.get_random_empty_cell()
            distance = math.hypot(self.dest_x - self.user_x, self.dest_y - self.user_y)
            if distance > ENV_WIDTH // 2:
                break

        self.canvas = tk.Canvas(root, width=ENV_WIDTH * CELL_SIZE, height=ENV_HEIGHT * CELL_SIZE, bg="white")
        self.canvas.pack(padx=10, pady=10)

        self.status_label = tk.Label(root, text="Status: Awaiting AI movement...", font=("Helvetica", 10))
        self.status_label.pack()

        self.log = tk.Text(root, height=8, width=70)
        self.log.pack(padx=10, pady=5)

        self.legend_label = tk.Label(root, text=self.get_legend_text(), font=("Courier", 9), justify="left")
        self.legend_label.pack()

        self.generate_static_environment()
        self.place_moving_objects()
        self.draw_environment()
        self.root.after(1000, self.move_ai_step)
        self.root.after(1000, self.update_moving_objects)

    def get_legend_text(self):
        legend = [f"{props['key']} = {name}" for name, props in object_types.items()]
        legend += ["U = AI User", "D = Destination", "Path = Light Yellow Trail"]
        return "\n".join(legend)

    def log_action(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)

    def get_random_empty_cell(self):
        while True:
            x, y = random.randint(0, ENV_WIDTH-1), random.randint(0, ENV_HEIGHT-1)
            if self.env[y][x] is None and (x, y) not in self.moving_objects_positions:
                return x, y

    def generate_static_environment(self):
        for _ in range(60):
            x, y = self.get_random_empty_cell()
            self.env[y][x] = random.choice(list(static_objects))

    def place_moving_objects(self):
        self.moving_objects_positions = []
        while len(self.moving_objects_positions) < MOVING_OBJECT_COUNT:
            x, y = self.get_random_empty_cell()
            if (x, y) not in self.moving_objects_positions and (x, y) != (self.user_x, self.user_y) and (x, y) != (self.dest_x, self.dest_y):
                obj = random.choice(list(moving_objects))
                self.env[y][x] = obj
                self.moving_objects_positions.append((x, y))

    def update_moving_objects(self):
        new_positions = []
        for (x, y) in self.moving_objects_positions:
            obj = self.env[y][x]
            self.env[y][x] = None  # clear old position

            directions = [(-1,0), (1,0), (0,-1), (0,1)]
            random.shuffle(directions)
            moved = False

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < ENV_WIDTH and 0 <= ny < ENV_HEIGHT and
                    self.env[ny][nx] is None and (nx, ny) != (self.user_x, self.user_y) and (nx, ny) != (self.dest_x, self.dest_y) and (nx, ny) not in new_positions):
                    self.env[ny][nx] = obj
                    new_positions.append((nx, ny))
                    moved = True
                    break

            if not moved:
                self.env[y][x] = obj
                new_positions.append((x, y))

        self.moving_objects_positions = new_positions
        self.draw_environment()
        self.root.after(1000, self.update_moving_objects)

    def draw_environment(self):
        self.canvas.delete("all")

        for (x, y) in self.path_trail:
            self.canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill="lightyellow", outline=""
            )

        for y in range(ENV_HEIGHT):
            for x in range(ENV_WIDTH):
                obj = self.env[y][x]
                color = object_types[obj]['color'] if obj else 'white'
                self.canvas.create_rectangle(
                    x * CELL_SIZE, y * CELL_SIZE, (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                    fill=color, outline="black"
                )
                if obj:
                    self.canvas.create_text(
                        x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2,
                        text=object_types[obj]['key'], fill="white"
                    )

        self.canvas.create_rectangle(
            self.dest_x * CELL_SIZE, self.dest_y * CELL_SIZE,
            (self.dest_x + 1) * CELL_SIZE, (self.dest_y + 1) * CELL_SIZE,
            fill="lightblue"
        )
        self.canvas.create_text(
            self.dest_x * CELL_SIZE + CELL_SIZE // 2, self.dest_y * CELL_SIZE + CELL_SIZE // 2,
            text="D", fill="black", font=("Helvetica", 10, "bold")
        )

        self.canvas.create_oval(
            self.user_x * CELL_SIZE + 5, self.user_y * CELL_SIZE + 5,
            (self.user_x + 1) * CELL_SIZE - 5, (self.user_y + 1) * CELL_SIZE - 5,
            fill="yellow"
        )
        self.canvas.create_text(
            self.user_x * CELL_SIZE + CELL_SIZE // 2, self.user_y * CELL_SIZE + CELL_SIZE // 2,
            text="U", fill="black", font=("Helvetica", 10, "bold")
        )

    def get_direction_message(self, current_x, current_y, next_x, next_y):
        direction = ""
        if next_x < current_x:
            direction = "Object ahead, move left."
        elif next_x > current_x:
            direction = "Object ahead, move right."
        elif next_y < current_y:
            direction = "Object ahead, move up."
        elif next_y > current_y:
            direction = "Object ahead, move down."
        return direction

    def detect_nearby_objects(self):
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = self.user_x + dx, self.user_y + dy
            if 0 <= nx < ENV_WIDTH and 0 <= ny < ENV_HEIGHT:
                obj = self.env[ny][nx]
                if obj:
                    self.log_action(f"AI detected nearby object: {obj}")

    def move_ai_step(self):
        path = dijkstra(self.env, (self.user_x, self.user_y), (self.dest_x, self.dest_y))
        
        if not path or len(path) <= 1:
            self.log_action("AI cannot move further or already at destination.")
            self.status_label.config(text="Status: AI Stopped.")
            self.show_final_path()
            return

        next_x, next_y = path[1]
        
        # Print direction message to guide the user
        direction_message = self.get_direction_message(self.user_x, self.user_y, next_x, next_y)
        self.log_action(direction_message)

        self.path_trail.append((self.user_x, self.user_y))
        self.user_x, self.user_y = next_x, next_y
        self.detect_nearby_objects()
        self.draw_environment()

        if (self.user_x, self.user_y) == (self.dest_x, self.dest_y):
            self.log_action("AI reached destination.")
            self.status_label.config(text="Status: Destination Reached.")
            self.show_final_path()
        else:
            self.root.after(1000, self.move_ai_step)  # Delay before next move

    def show_final_path(self):
        # Draw the final path taken by the AI in green
        for (x, y) in self.path_trail:
            self.canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill="lightgreen", outline=""
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartAssistantApp(root)
    root.mainloop()

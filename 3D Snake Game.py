import sys
import random
import time
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Game constants
GRID_SIZE = 20
CELL_SIZE = 1.0
MOVE_INTERVAL = 0.15
SPEED_CHANGE_DURATION = 5
COLOR_CHANGE_DURATION = 5
MAX_FOODS = 5

# Food types
NORMAL_FOOD = 0
GOLDEN_FOOD = 1
SPEED_FOOD = 2
SLOW_FOOD = 3
POISON_FOOD = 4

# Difficulty levels
EASY = 0
MEDIUM = 1
HARD = 2

class SnakeSegment:
    def __init__(self, position, direction):
        self.position = position
        self.direction = direction
        self.target_position = position
        self.target_direction = direction
        self.animation_progress = 1.0

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        initial_pos = (0, 0, 0)
        initial_dir = (1, 0, 0)  # Start facing right
        self.segments = [SnakeSegment(initial_pos, initial_dir)]
        self.grow_pending = 2
        self.direction = initial_dir
        self.base_color = self.generate_random_color()
        self.current_color = self.base_color
        self.speed_multiplier = 1.0
        self.color_change_time = 0
        self.speed_change_time = 0
        self.last_color_change = 0
        self.length = 1
        
    def generate_random_color(self):
        return (
            random.uniform(0.2, 0.8),
            random.uniform(0.2, 0.8),
            random.uniform(0.2, 0.8)
        )
        
    def move(self):
        current_time = time.time()
        
        if current_time > self.speed_change_time:
            self.speed_multiplier = 1.0
            
        if current_time > self.color_change_time and self.current_color != self.base_color:
            if not (self.speed_multiplier != 1.0 and current_time < self.speed_change_time):
                self.current_color = self.base_color
            
        move_speed = 0.5 * self.speed_multiplier
        for segment in self.segments:
            if segment.animation_progress < 1.0:
                segment.animation_progress = min(1.0, segment.animation_progress + move_speed)
                t = segment.animation_progress
                segment.position = (
                    segment.position[0] * (1-t) + segment.target_position[0] * t,
                    segment.position[1] * (1-t) + segment.target_position[1] * t,
                    segment.position[2] * (1-t) + segment.target_position[2] * t
                )
                segment.direction = (
                    segment.direction[0] * (1-t) + segment.target_direction[0] * t,
                    segment.direction[1] * (1-t) + segment.target_direction[1] * t,
                    segment.direction[2] * (1-t) + segment.target_direction[2] * t
                )
        
        if self.segments[0].animation_progress >= 1.0:
            head = self.segments[0]
            new_head_pos = (
                head.target_position[0] + self.direction[0],
                head.target_position[1] + self.direction[1],
                head.target_position[2] + self.direction[2]
            )
            
            prev_pos = head.target_position
            prev_dir = head.target_direction
            head.target_position = new_head_pos
            head.target_direction = self.direction
            head.animation_progress = 0.0
            
            for i in range(1, len(self.segments)):
                current_segment = self.segments[i]
                temp_pos = current_segment.target_position
                temp_dir = current_segment.target_direction
                current_segment.target_position = prev_pos
                current_segment.target_direction = prev_dir
                current_segment.animation_progress = 0.0
                prev_pos = temp_pos
                prev_dir = temp_dir
                
            if self.grow_pending > 0:
                self.segments.append(SnakeSegment(prev_pos, prev_dir))
                self.grow_pending -= 1
                self.length += 1
            
    def change_direction(self, new_dir):
        if (new_dir[0] * -1, new_dir[1] * -1, new_dir[2] * -1) != self.direction:
            self.direction = new_dir
            
    def grow(self, amount):
        self.grow_pending += amount
        
    def check_collision(self, obstacles):
        for segment in self.segments:
            seg_pos = segment.target_position
            
            if (abs(seg_pos[0]) >= GRID_SIZE // 2 or 
                abs(seg_pos[1]) >= GRID_SIZE // 2 or 
                abs(seg_pos[2]) >= GRID_SIZE // 2):
                return True
                
            for obstacle in obstacles:
                if obstacle.check_collision(seg_pos):
                    return True
        
        head_pos = self.segments[0].target_position
        for segment in self.segments[1:]:
            if segment.target_position == head_pos:
                return True
                
        return False
        
    def apply_food_effect(self, food_type):
        current_time = time.time()
        
        if food_type == NORMAL_FOOD:
            self.grow(1)
        elif food_type == GOLDEN_FOOD:
            self.grow(3)
            self.current_color = (0.9, 0.8, 0.1)
            self.color_change_time = current_time + COLOR_CHANGE_DURATION
        elif food_type == SPEED_FOOD:
            self.speed_multiplier = 2.0
            self.speed_change_time = current_time + SPEED_CHANGE_DURATION
            self.current_color = (0.0, 0.0, 1.0)
        elif food_type == SLOW_FOOD:
            self.speed_multiplier = 0.5
            self.speed_change_time = current_time + SPEED_CHANGE_DURATION
            self.current_color = (0.6, 0.2, 0.8)
        elif food_type == POISON_FOOD:
            if self.length > 3:
                self.segments = self.segments[:-2]
                self.length -= 2
            self.current_color = (0.0, 1.0, 0.0)
            self.color_change_time = current_time + COLOR_CHANGE_DURATION

class Food:
    def __init__(self):
        self.position = (0, 0, 0)
        self.type = NORMAL_FOOD
        self.spawn_time = 0
        self.duration = 8
        self.active = False
        self.rotation = 0
        
    def spawn(self, snake_segments, obstacles):
        while True:
            self.position = (
                random.randint(-GRID_SIZE//2 + 1, GRID_SIZE//2 - 1),
                0,
                random.randint(-GRID_SIZE//2 + 1, GRID_SIZE//2 - 1)
            )
            
            occupied = any(seg.target_position == self.position for seg in snake_segments)
            if occupied:
                continue
                
            if any(obs.position == self.position and obs.is_active for obs in obstacles):
                continue
                
            break
            
        rand = random.random()
        if rand < 0.6:
            self.type = NORMAL_FOOD
            self.duration = 8
        elif rand < 0.8:
            self.type = GOLDEN_FOOD
            self.duration = 8
        elif rand < 0.9:
            self.type = SPEED_FOOD
            self.duration = 8
        elif rand < 0.95:
            self.type = SLOW_FOOD
            self.duration = 10
        else:
            self.type = POISON_FOOD
            self.duration = 8
            
        self.spawn_time = time.time()
        self.active = True
        self.rotation = random.uniform(0, 360)
        
    def update(self):
        if self.active:
            self.rotation = (self.rotation + 0.5) % 360
        
    def check_expired(self):
        if not self.active:
            return False
        return time.time() > self.spawn_time + self.duration
        
    def draw(self):
        if not self.active:
            return
            
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.rotation, 0, 1, 0)
        
        if self.type == NORMAL_FOOD:
            glColor3f(1.0, 0.0, 0.0)
            glutSolidSphere(0.4, 16, 16)
            glColor3f(1.0, 1.0, 1.0)
            glPushMatrix()
            glTranslatef(0.3, 0.3, 0.3)
            glutSolidSphere(0.1, 8, 8)
            glPopMatrix()
        elif self.type == GOLDEN_FOOD:
            glColor3f(0.9, 0.8, 0.1)
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 0.6, 0)
            for i in range(6):
                angle = math.pi * 2 * i / 5
                outer_x = math.sin(angle) * 0.5
                outer_z = math.cos(angle) * 0.5
                inner_x = math.sin(angle + math.pi/5) * 0.2
                inner_z = math.cos(angle + math.pi/5) * 0.2
                glVertex3f(outer_x, 0.1, outer_z)
                glVertex3f(inner_x, 0.3, inner_z)
            glEnd()
        elif self.type == SPEED_FOOD:
            glColor3f(0.0, 0.0, 1.0)
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 0.5, 0)
            glVertex3f(-0.2, 0.2, 0)
            glVertex3f(0.2, 0.2, 0)
            glVertex3f(0.2, 0.2, 0)
            glVertex3f(-0.2, 0.2, 0)
            glVertex3f(-0.3, -0.2, 0)
            glVertex3f(0.3, -0.2, 0)
            glVertex3f(0.3, -0.2, 0)
            glVertex3f(-0.3, -0.2, 0)
            glVertex3f(0, -0.5, 0)
            glEnd()
        elif self.type == SLOW_FOOD:
            glColor3f(0.6, 0.2, 0.8)
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 0.5, 0)
            for i in range(5):
                angle = math.pi * 2 * i / 4
                glVertex3f(math.sin(angle) * 0.3, 0.2, math.cos(angle) * 0.3)
            glEnd()
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, -0.5, 0)
            for i in range(5):
                angle = math.pi * 2 * i / 4
                glVertex3f(math.sin(angle) * 0.3, -0.2, math.cos(angle) * 0.3)
            glEnd()
            glBegin(GL_QUADS)
            glVertex3f(-0.2, 0.0, -0.2)
            glVertex3f(0.2, 0.0, -0.2)
            glVertex3f(0.2, 0.0, 0.2)
            glVertex3f(-0.2, 0.0, 0.2)
            glEnd()
        elif self.type == POISON_FOOD:
            glColor3f(0.0, 1.0, 0.0)
            glutSolidSphere(0.4, 16, 16)
            glColor3f(0.2, 0.2, 0.2)
            glPushMatrix()
            glTranslatef(-0.15, 0.1, 0.35)
            glutSolidSphere(0.1, 8, 8)
            glTranslatef(0.3, 0, 0)
            glutSolidSphere(0.1, 8, 8)
            glPopMatrix()
            glColor3f(1.0, 1.0, 1.0)
            for i in range(4):
                offset = i * 0.15 - 0.225
                glPushMatrix()
                glTranslatef(offset, -0.3, 0.35)
                glutSolidCube(0.1)
                glPopMatrix()
            
        glPopMatrix()

class Obstacle:
    def __init__(self, position, difficulty, is_boundary=False):
        self.position = list(position)
        self.difficulty = difficulty
        self.is_boundary = is_boundary
        self.rotation = random.uniform(0, 360)
        self.scale = random.uniform(0.8, 1.2)
        self.color = (
            random.uniform(0.2, 1.0),
            random.uniform(0.2, 1.0),
            random.uniform(0.2, 1.0)
        )
        self.is_active = True
        self.move_direction = [0, 0, 0]
        self.move_speed = 0.0
        self.move_range = 0.0
        self.origin = list(position)
        self.pulse_factor = 0.0
        self.pulse_speed = random.uniform(0.05, 0.1)
        
        if difficulty == HARD and not is_boundary:
            axis = random.choice([0, 2])  # X or Z axis
            self.move_direction[axis] = random.choice([-1, 1])
            self.move_speed = random.uniform(0.04, 0.06)
            self.move_range = random.uniform(3.0, 4.0)
            
    def update(self):
        if self.difficulty == HARD and self.is_active and not self.is_boundary:
            self.pulse_factor = (math.sin(time.time() * self.pulse_speed) + 1) / 2
            
            new_pos = [
                self.position[0] + self.move_direction[0] * self.move_speed,
                self.position[1],
                self.position[2] + self.move_direction[2] * self.move_speed
            ]
            
            boundary_min = -GRID_SIZE//2 + 1
            boundary_max = GRID_SIZE//2 - 1
            
            if new_pos[0] < boundary_min or new_pos[0] > boundary_max:
                self.move_direction[0] *= -1
                new_pos[0] = max(boundary_min, min(boundary_max, new_pos[0]))
                
            if new_pos[2] < boundary_min or new_pos[2] > boundary_max:
                self.move_direction[2] *= -1
                new_pos[2] = max(boundary_min, min(boundary_max, new_pos[2]))
            
            self.position = new_pos
        
    def check_collision(self, position):
        if not self.is_active:
            return False
            
        dx = position[0] - self.position[0]
        dz = position[2] - self.position[2]
        distance = math.sqrt(dx*dx + dz*dz)
        return distance < 0.8
        
    def draw(self):
        if not self.is_active:
            return
            
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.rotation, 0, 1, 0)
        glScalef(self.scale, self.scale, self.scale)
        
        if self.difficulty == HARD and not self.is_boundary:
            pulse_color = (
                min(1.0, self.color[0] + self.pulse_factor * 0.3),
                max(0.2, self.color[1] - self.pulse_factor * 0.2),
                self.color[2]
            )
            glColor3f(*pulse_color)
        else:
            glColor3f(*self.color)
            
        glutSolidCube(0.9)
        glColor3f(0.7, 0.7, 0.7)
        glLineWidth(2.0)
        glutWireCube(0.91)
        
        if self.difficulty == HARD and not self.is_boundary:
            glPushMatrix()
            glTranslatef(0, 0.6, 0)
            glColor3f(1.0, 0.0, 0.0)
            if self.move_direction[0] != 0:
                glRotatef(90 if self.move_direction[0] > 0 else -90, 0, 0, 1)
            else:
                glRotatef(0 if self.move_direction[2] > 0 else 180, 0, 1, 0)
            glutSolidCone(0.15, 0.3, 8, 1)
            glPopMatrix()
        
        glPopMatrix()

class Game:
    def __init__(self):
        self.snake = Snake()
        self.foods = []
        self.obstacles = []
        self.score = 0
        self.game_over = False
        self.paused = False
        self.last_move_time = 0
        self.next_food_spawn = time.time() + random.uniform(1, 3)
        self.camera_mode = 2  # Start with top-down view
        self.camera_angle_x = 30
        self.camera_angle_y = 45
        self.camera_distance = 15
        self.difficulty = EASY
        self.selecting_difficulty = True
        self.last_obstacle_move = 0
        self.obstacle_move_interval = 0.02
        
    def generate_obstacles(self):
        self.obstacles = []
        
        wall_color = (1.0, 0.0, 0.0)
        for x in range(-GRID_SIZE//2, GRID_SIZE//2 + 1):
            for z in [-GRID_SIZE//2, GRID_SIZE//2]:
                obstacle = Obstacle((x, 0, z), self.difficulty, is_boundary=True)
                obstacle.color = wall_color
                self.obstacles.append(obstacle)
        for z in range(-GRID_SIZE//2 + 1, GRID_SIZE//2):
            for x in [-GRID_SIZE//2, GRID_SIZE//2]:
                obstacle = Obstacle((x, 0, z), self.difficulty, is_boundary=True)
                obstacle.color = wall_color
                self.obstacles.append(obstacle)
    
        obstacle_count = {
            EASY: 0,
            MEDIUM: 10,
            HARD: 5  # 5 moving obstacles in Hard mode
        }[self.difficulty]
        
        for _ in range(obstacle_count):
            while True:
                pos = (
                    random.randint(-GRID_SIZE//2 + 1, GRID_SIZE//2 - 1),
                    0,
                    random.randint(-GRID_SIZE//2 + 1, GRID_SIZE//2 - 1)
                )
                if not any(seg.target_position == pos for seg in self.snake.segments) and pos != (0, 0, 0):
                    self.obstacles.append(Obstacle(pos, self.difficulty))
                    break
                    
    def update_obstacles(self):
        current_time = time.time()
        if current_time - self.last_obstacle_move > self.obstacle_move_interval:
            for obstacle in self.obstacles:
                obstacle.update()
            self.last_obstacle_move = current_time
                
    def update(self):
        if self.game_over or self.paused or self.selecting_difficulty:
            return
            
        current_time = time.time()
        
        self.update_obstacles()
        
        if len(self.foods) < MAX_FOODS and current_time > self.next_food_spawn:
            new_food = Food()
            new_food.spawn(self.snake.segments, self.obstacles)
            self.foods.append(new_food)
            self.next_food_spawn = current_time + random.uniform(1, 3)
            
        for food in self.foods[:]:
            food.update()
            if food.check_expired():
                self.foods.remove(food)
                
        move_interval = MOVE_INTERVAL / self.snake.speed_multiplier
        if current_time - self.last_move_time > move_interval:
            if self.camera_mode != 0:  # Normal movement for other camera modes
                self.snake.move()
            else:  # First-person mode - always move forward
                self.snake.move()
            self.last_move_time = current_time
            
            head_pos = self.snake.segments[0].target_position
            for food in self.foods[:]:
                if food.position == head_pos:
                    self.snake.apply_food_effect(food.type)
                    self.score += 1 if food.type == NORMAL_FOOD else 3
                    self.foods.remove(food)
                
            if self.snake.check_collision(self.obstacles):
                self.game_over = True
                
    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        if not self.selecting_difficulty:
            head_pos = self.snake.segments[0].target_position if len(self.snake.segments) > 0 else (0, 0, 0)
            head_dir = self.snake.direction if len(self.snake.segments) > 0 else (0, 0, -1)
            
            if self.camera_mode == 0:  # First-Person View
                # Calculate look direction based on snake's direction
                look_at = (
                    head_pos[0] + head_dir[0],
                    head_pos[1] + head_dir[1],
                    head_pos[2] + head_dir[2]
                )
                gluLookAt(
                    head_pos[0], head_pos[1] + 0.5, head_pos[2],  # Camera at head position
                    look_at[0], head_pos[1] + 0.5, look_at[2],    # Looking where snake is going
                    0, 1, 0                                       # Up vector
                )
            elif self.camera_mode == 1:  # Third-person
                if len(self.snake.segments) > 1:
                    tail_dir = (
                        head_pos[0] - self.snake.segments[1].target_position[0],
                        head_pos[1] - self.snake.segments[1].target_position[1],
                        head_pos[2] - self.snake.segments[1].target_position[2]
                    )
                    length = math.sqrt(tail_dir[0]**2 + tail_dir[1]**2 + tail_dir[2]**2)
                    if length > 0:
                        tail_dir = (tail_dir[0]/length, tail_dir[1]/length, tail_dir[2]/length)
                else:
                    tail_dir = (0, 0, -1)
                    
                cam_pos = (
                    head_pos[0] - tail_dir[0] * 3,
                    head_pos[1] + 1.5,
                    head_pos[2] - tail_dir[2] * 3
                )
                
                gluLookAt(
                    cam_pos[0], cam_pos[1], cam_pos[2],
                    head_pos[0], head_pos[1] + 0.5, head_pos[2],
                    0, 1, 0
                )
            elif self.camera_mode == 2:  # Top-down
                gluLookAt(
                    0, 20, 0.1,
                    0, 0, 0,
                    0, 0, -1
                )
            elif self.camera_mode == 3:  # Free-look
                gluLookAt(0, 0, -self.camera_distance,
                          0, 0, 0,
                          0, 1, 0)
                glRotatef(self.camera_angle_x, 1, 0, 0)
                glRotatef(self.camera_angle_y, 0, 1, 0)
        
        glColor3f(0.4, 0.8, 0.4)
        glBegin(GL_QUADS)
        glVertex3f(-GRID_SIZE//2, -0.5, -GRID_SIZE//2)
        glVertex3f(GRID_SIZE//2, -0.5, -GRID_SIZE//2)
        glVertex3f(GRID_SIZE//2, -0.5, GRID_SIZE//2)
        glVertex3f(-GRID_SIZE//2, -0.5, GRID_SIZE//2)
        glEnd()
        
        for i, segment in enumerate(self.snake.segments):
            glPushMatrix()
            pos = segment.position
            glTranslatef(*pos)
            dx, dy, dz = segment.direction
            if dx != 0 or dz != 0:
                angle = math.degrees(math.atan2(dx, dz))
                glRotatef(angle, 0, 1, 0)
            
            if i == 0:
                glColor3f(*self.snake.current_color)
                glutSolidSphere(0.5, 16, 16)
                glColor3f(1.0, 1.0, 1.0)
                glPushMatrix()
                glTranslatef(0.2, 0.2, 0.3)
                glutSolidSphere(0.1, 8, 8)
                glTranslatef(-0.4, 0, 0)
                glutSolidSphere(0.1, 8, 8)
                glPopMatrix()
            else:
                size = 0.4 * (0.9 + 0.1 * (i / len(self.snake.segments)))
                color_factor = 0.7 + 0.3 * (i / len(self.snake.segments))
                glColor3f(
                    self.snake.current_color[0] * color_factor,
                    self.snake.current_color[1] * color_factor,
                    self.snake.current_color[2] * color_factor
                )
                glutSolidSphere(size, 12, 12)
            glPopMatrix()
            
        for food in self.foods:
            food.draw()
            
        for obstacle in self.obstacles:
            obstacle.draw()
            
        camera_modes = ["First-Person", "Third-Person", "Top-Down", "Free-Look"]
        difficulties = ["Easy", "Medium", "Hard"]
        
        if not self.selecting_difficulty:
            self.draw_text(f"Score: {self.score}", -0.9, 0.9)
            self.draw_text(f"Length: {self.snake.length}", -0.9, 0.8)
            self.draw_text(f"Difficulty: {difficulties[self.difficulty]}", -0.9, 0.7)
            self.draw_text(f"Camera: {camera_modes[self.camera_mode]}", -0.9, 0.6)
            self.draw_text("WASD: Move | C: Camera | P: Pause | R: Restart", -0.9, -0.9)
            
            if self.game_over:
                self.draw_text("GAME OVER", -0.2, 0)
                self.draw_text("Press R to restart", -0.3, -0.1)
                
            if self.paused:
                self.draw_text("PAUSED", -0.15, 0)
        else:
            glColor3f(1.0, 1.0, 1.0)
            self.draw_text("Select Difficulty", -0.3, 0.5)
            
            glColor3f(1.0, 1.0, 0.0)
            if self.difficulty == EASY:
                self.draw_text("> EASY <", -0.15, 0.2)
            else:
                self.draw_text("EASY", -0.1, 0.2)
                
            if self.difficulty == MEDIUM:
                self.draw_text("> MEDIUM <", -0.2, 0.0)
            else:
                self.draw_text("MEDIUM", -0.15, 0.0)
                
            if self.difficulty == HARD:
                self.draw_text("> HARD <", -0.15, -0.2)
            else:
                self.draw_text("HARD", -0.1, -0.2)
                
            glColor3f(1.0, 1.0, 1.0)
            self.draw_text("Press ENTER to start", -0.3, -0.5)
            self.draw_text("Use UP/DOWN arrows to select", -0.4, -0.6)
            
        glutSwapBuffers()
            
    def draw_text(self, text, x, y):
        glColor3f(1.0, 1.0, 1.0)
        glWindowPos2f(x * glutGet(GLUT_WINDOW_WIDTH)/2 + glutGet(GLUT_WINDOW_WIDTH)/2, 
                      y * glutGet(GLUT_WINDOW_HEIGHT)/2 + glutGet(GLUT_WINDOW_HEIGHT)/2)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
            
    def reset(self):
        self.snake = Snake()
        self.foods = []
        self.score = 0
        self.game_over = False
        self.paused = False
        self.last_move_time = time.time()
        self.next_food_spawn = time.time() + random.uniform(1, 3)
        self.generate_obstacles()
        self.last_obstacle_move = time.time()

def init():
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, [50])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

def display():
    game.draw()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = float(w)/float(h)
    gluPerspective(45 if game.camera_mode != 2 else 60, aspect, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def keyboard(key, x, y):
    global game
    
    key = key.decode('utf-8').lower()
    
    if game.selecting_difficulty:
        if key == '\r' or key == '\n':
            game.selecting_difficulty = False
            game.reset()
        return
    
    if key == 'r' and game.game_over:
        game.reset()
    elif key == 'p':
        game.paused = not game.paused
    elif key == 'c':
        game.camera_mode = (game.camera_mode + 1) % 4
        glutPostRedisplay()
    elif not game.game_over and not game.paused:
        if game.camera_mode == 0:  # First-person controls
            if key == 'a':  # Turn left
                # Rotate direction 90 degrees left
                current_dir = game.snake.direction
                new_dir = (current_dir[2], 0, -current_dir[0])
                game.snake.change_direction(new_dir)
            elif key == 'd':  # Turn right
                # Rotate direction 90 degrees right
                current_dir = game.snake.direction
                new_dir = (-current_dir[2], 0, current_dir[0])
                game.snake.change_direction(new_dir)
        else:  # Other camera modes
            if key == 'w':
                game.snake.change_direction((0, 0, -1))
            elif key == 's':
                game.snake.change_direction((0, 0, 1))
            elif key == 'a':
                game.snake.change_direction((-1, 0, 0))
            elif key == 'd':
                game.snake.change_direction((1, 0, 0))
            
    glutPostRedisplay()

def special_keys(key, x, y):
    global game
    
    if game.selecting_difficulty:
        if key == GLUT_KEY_UP:
            game.difficulty = max(EASY, game.difficulty - 1)
        elif key == GLUT_KEY_DOWN:
            game.difficulty = min(HARD, game.difficulty + 1)
        glutPostRedisplay()
        return
    
    if game.camera_mode == 3:  # Free-look camera
        if key == GLUT_KEY_UP:
            game.camera_angle_x = min(game.camera_angle_x + 5, 90)
        elif key == GLUT_KEY_DOWN:
            game.camera_angle_x = max(game.camera_angle_x - 5, -90)
        elif key == GLUT_KEY_LEFT:
            game.camera_angle_y = (game.camera_angle_y - 5) % 360
        elif key == GLUT_KEY_RIGHT:
            game.camera_angle_y = (game.camera_angle_y + 5) % 360
            
    glutPostRedisplay()

def idle():
    if not game.selecting_difficulty:
        game.update()
    glutPostRedisplay()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 750)
    glutCreateWindow(b"3D Snake Game - Final Version")
    
    init()
    
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    game = Game()
    main()
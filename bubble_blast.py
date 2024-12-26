from pathlib import Path
import pygame
import random
from pygame import Surface, mixer
import numpy as np
import math
import cv2

# message class to display text on screen
class Message:
    def __init__(self, text, duration=2000):  # duration in milliseconds
        self.text = text
        self.creation_time = pygame.time.get_ticks()
        self.duration = duration
        
        # make a font library for emoji support
        emoji_fonts = ['Apple Color Emoji', 'Noto Color Emoji','Segoe UI Emoji', 'Arial Unicode MS', 'Arial']
        self.font = None
        
        print("\nTrying to load emoji fonts...")
        for font_name in emoji_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 36)
                # Test if font can render an emoji
                test = self.font.render('😊', True, (255, 255, 255))
                print(f"Successfully loaded {font_name}!")
                break
            except Exception as e:
                print(f"Failed to load {font_name}: {str(e)}")
                continue
        
        # Fallback to default if no emoji font works
        if self.font is None:
            self.font = pygame.font.Font(None, 36)
        
        self.color = (255, 255, 255)  # White text
        self.alpha = 255  # For fade out effect
        self.y_offset = 0  # Each message will get its own y-offset
        

    def is_expired(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.creation_time > self.duration

    def draw(self, screen):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.creation_time
        time_left = self.duration - elapsed_time
        
        # Fade out effect in the last 500ms
        if time_left < 500:
            self.alpha = max(0, min(255, int((time_left / 500) * 255)))
        
        try:
            text_surface = self.font.render(self.text, True, self.color)
        except:
            # If emoji fails, use simplified text
            simplified_text = (self.text.replace('🌬', '*')
                             .replace('✨', '*')
                             .replace('🌟', '*')
                             .replace('🎵', '*')
                             .replace('👋', '*')
                             .replace('❌', 'X')
                             .replace('🌀', '@')
                             .replace('🌊', '~'))
            text_surface = self.font.render(simplified_text, True, self.color)
        
        text_surface.set_alpha(self.alpha)
        
        # Position the text at the top center of the screen
        x = (screen.get_width() - text_surface.get_width()) // 2
        y = 20 + self.y_offset  # Offset each message vertically
        screen.blit(text_surface, (x, y))

# Bubble class to create and manage bubbles
class BlowEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = 100
        self.particles = []
        self.lifetime = 30

    def update(self):
        self.radius += 8
        self.lifetime -= 1
        
        # Add new particles
        if self.lifetime > 15:  # Only add particles in first half of animation
            for _ in range(3):
                angle = random.uniform(0, math.pi)
                speed = random.uniform(2, 5)
                self.particles.append({
                    'x': self.x,
                    'y': self.y,
                    'dx': math.cos(angle) * speed,
                    'dy': -math.sin(angle) * speed,
                    'life': random.randint(10, 20)
                })
        
        # Update existing particles
        for particle in self.particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
        
        self.particles = [p for p in self.particles if p['life'] > 0]
        
        return self.lifetime > 0

    def draw(self, screen):
        # Draw expanding circles
        alpha = int(255 * (self.lifetime / 30))
        surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 255, 255, alpha), (self.radius, self.radius), self.radius, 2)
        screen.blit(surface, (self.x - self.radius, self.y - self.radius))
        
        # Draw particles
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 20))
            pygame.draw.circle(screen, (200, 200, 255, alpha), 
                             (int(particle['x']), int(particle['y'])), 2)

class BubbleParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.dx = random.uniform(-3, 3)
        self.dy = random.uniform(-3, 3)
        self.lifetime = 60
        self.color = color
        self.radius = random.randint(2, 4)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 2
        self.radius *= 0.95

class Bubble:
    def __init__(self, x, y, screen_width, screen_height):
        self.x = x
        self.y = y
        self.radius = random.randint(15, 35)
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-3, -1)
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(200, 255),
            random.randint(100, 200),
        )
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.lifetime = 255
        self.wobble_phase = random.uniform(0, 2 * math.pi)
        self.wobble_speed = random.uniform(0.05, 0.1)
        self.burst = False
        self.particles = []

    def move(self):
        if self.burst:
            for particle in self.particles:
                particle.update()
            self.particles = [p for p in self.particles if p.lifetime > 0]
            return len(self.particles) > 0

        self.x += self.dx
        self.y += self.dy
        self.dy += 0.02
        self.lifetime -= 1

        self.wobble_phase += self.wobble_speed
        self.dx += math.sin(self.wobble_phase) * 0.1

        if self.x - self.radius <= 0 or self.x + self.radius >= self.screen_width:
            self.dx *= -0.8

        return self.lifetime > 0 and self.y + self.radius > 0

    def burst_bubble(self):
        self.burst = True
        
        # Play pop sound
        pygame.mixer.Channel(0).play(pygame.mixer.Sound("pop.wav"))
        
        for _ in range(15):
            self.particles.append(BubbleParticle(self.x, self.y, self.color))
    
    #add wind motion to bubbles
    def apply_wind(self, force_x, force_y):
        self.dx += force_x
        self.dy += force_y

    def draw(self, screen):
        if self.burst:
            for particle in self.particles:
                color = (*self.color[:3], int(particle.lifetime * 3))
                surface = pygame.Surface((particle.radius * 2, particle.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surface, color, (particle.radius, particle.radius), particle.radius)
                screen.blit(surface, (particle.x - particle.radius, particle.y - particle.radius))
        else:
            color = (*self.color[:3], int(self.lifetime))
            surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, color, (self.radius, self.radius), self.radius)
            shimmer_pos = (
                self.radius + math.cos(self.wobble_phase) * (self.radius * 0.3),
                self.radius + math.sin(self.wobble_phase) * (self.radius * 0.3),
            )
            pygame.draw.circle(surface, (255, 255, 255, 100), shimmer_pos, self.radius * 0.2)
            screen.blit(surface, (self.x - self.radius, self.y - self.radius))

class BubbleGame:
    def __init__(self):
        pygame.init()
        
        try:
            mixer.init()
            print("Mixer initialized successfully.")
        except Exception as e:
            print(f"Error initializing mixer: {e}")
        
        # set up sound channels
        pygame.mixer.set_num_channels(8)

        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🌟 Bubble Blast Fun ✨")
        
        self.startup_time = pygame.time.get_ticks()
        self.startup_delay = 2000  # 2 seconds delay
        self.first_blow = False # Flag to check if first blow has occurred
        self.bubbles = []
        self.blow_effects = []
        self.hand_trails = []
        self.messages = []  # New list to store active messages
        self.running = True
        self.motion_threshold = 20
        self.prev_frame = None
        self.last_blow_time = 0
        self.blow_cooldown = 300
        self.current_pattern = "fountain"
        self.pattern_change_time = 0
        self.pattern_duration = 5000

        # Load and set up sounds
        try:
            self.pop_sound = pygame.mixer.Sound("pop.wav")
            self.blow_sound = pygame.mixer.Sound("bubbles2.wav") 
            self.pop_sound.set_volume(0.4)  # Reduced volume to prevent it from being too loud
            if hasattr(self, 'blow_sound'):
                self.blow_sound.set_volume(0.4)
            self.add_message("🎵 Sounds loaded successfully!")
        except Exception as e:
            print(f"Sound error: {e}")  # This will help debug sound issues
            self.add_message("Note: Sound files not found", duration=3000)
            self.pop_sound = pygame.mixer.Sound(buffer=np.zeros(4410))
            self.pop_sound.set_volume(0)

        try:
            self.cv2 = cv2
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera_available = True
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.add_message("✨ Camera initialized! ✨")
                self.add_message("🌬 Blow to create bubbles!", duration=3000)
                self.add_message("👋 Wave hands to pop bubbles!", duration=3000)
            else:
                self.camera_available = False
                self.add_message("❌ Camera not available", duration=3000)
        except ImportError:
            self.cv2 = None
            self.camera_available = False
            self.add_message("❌ CV2 not installed", duration=3000)

    def add_message(self, text, duration=2000):
    # Calculate vertical offset based on existing messages
        y_offset = len(self.messages) * 40  # 40 pixels between messages
        msg = Message(text, duration)
        msg.y_offset = y_offset
        self.messages.append(msg)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.add_message("✨ All bubbles burst! ✨")
                    
                    pygame.mixer.Channel(2).play(self.pop_sound)
                    for bubble in self.bubbles:
                        if not bubble.burst:
                            bubble.burst_bubble()
                elif event.key == pygame.K_f:
                    self.current_pattern = "fountain"
                    self.add_message("🌬 Fountain pattern activated!")
                elif event.key == pygame.K_s:
                    self.current_pattern = "spiral"
                    self.add_message("🌀 Spiral pattern activated!")
                elif event.key == pygame.K_w:
                    self.current_pattern = "wave"
                    self.add_message("🌊 Wave pattern activated!")
    
    def check_camera_interaction(self):
        if not self.camera_available:
            return

        ret, frame = self.camera.read()
        if not ret:
            return

        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        blurred = self.cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = blurred
            return

        # Calculate frame difference
        frame_diff = self.cv2.absdiff(self.prev_frame, blurred)
        self.prev_frame = blurred

        # Detect blow - focus on vertical motion in center region
        center_region = frame_diff[frame_diff.shape[0]//2-40:frame_diff.shape[0]//2+40, 
                                 frame_diff.shape[1]//2-40:frame_diff.shape[1]//2+40]
        
        # Calculate vertical motion (more sensitive to blowing)
        vertical_motion = np.mean(center_region[:-1] - center_region[1:])
        
        current_time = pygame.time.get_ticks()
        if (current_time - self.startup_time > self.startup_delay and 
            vertical_motion > self.motion_threshold and 
            current_time - self.last_blow_time > self.blow_cooldown):
            
            self.first_blow = True # Set flag to True after first blow
            # Create blow effect
            effect = BlowEffect(self.screen_width//2, self.screen_height - 50)
            self.blow_effects.append(effect)
            
            # Play blow sound
            pygame.mixer.Channel(1).play(self.blow_sound)
            
            # Create stream of bubbles with current pattern
            if self.first_blow:
                self.create_bubble_stream(self.screen_width//2, self.screen_height - 50, 
                                        pattern=self.current_pattern, count=12)
            
            # Apply wind force to existing bubbles
            wind_force_x = random.uniform(-3, 3)  # Random horizontal force
            wind_force_y = random.uniform(-4, -2)  # Stronger upward force
            for bubble in self.bubbles:
                if not bubble.burst:
                    bubble.apply_wind(wind_force_x, wind_force_y)
            
            self.add_message("🌬 Woosh!", duration=1000)
            self.last_blow_time = current_time

        # Detect hand motion
        _, thresh = self.cv2.threshold(frame_diff, 25, 255, self.cv2.THRESH_BINARY)
        contours, _ = self.cv2.findContours(thresh, self.cv2.RETR_EXTERNAL, 
                                          self.cv2.CHAIN_APPROX_SIMPLE)

        # Update hand trails
        self.hand_trails = [(x, y, life-1) for x, y, life in self.hand_trails if life > 0]

        for contour in contours:
            if self.cv2.contourArea(contour) > 2000:
                M = self.cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Scale coordinates to match screen
                    x = int(cx * self.screen_width / frame.shape[1])
                    y = int(cy * self.screen_height / frame.shape[0])
                    
                    # Add to hand trails
                    self.hand_trails.append((x, y, 20))
                    
                    # Check for bubble collisions
                    center_x = self.screen_width // 2
                    center_y = self.screen_height // 2
                    if abs(x - center_x) > 100 or abs(y - center_y) > 100:  # Ignore center region
                        for bubble in self.bubbles:
                            if not bubble.burst:
                                x, y, w, h = self.cv2.boundingRect(contour)
                                x = int(x * self.screen_width / frame.shape[1])
                                y = int(y * self.screen_height / frame.shape[0])
                                w = int(w * self.screen_width / frame.shape[1])
                                h = int(h * self.screen_height / frame.shape[0])
                                
                                if x < bubble.x < x + w and y < bubble.y < y + h:
                                    bubble.burst_bubble()

    def update(self):
        self.handle_events()
        self.check_camera_interaction()
        
        # Update bubbles
        self.bubbles = [bubble for bubble in self.bubbles if bubble.move()]
        
        # Update blow effects
        self.blow_effects = [effect for effect in self.blow_effects if effect.update()]
        
        # Update messages - remove expired ones
        self.messages = [msg for msg in self.messages if not msg.is_expired()]

    def draw(self):
        # Create a gradient background
        for i in range(self.screen_height):
            color = (
                int(20 + (i / self.screen_height) * 20),
                int(20 + (i / self.screen_height) * 20),
                int(40 + (i / self.screen_height) * 40)
            )
            pygame.draw.line(self.screen, color, (0, i), (self.screen_width, i))

        # Draw hand trails
        for x, y, life in self.hand_trails:
            alpha = int(255 * (life / 20))
            radius = int(20 * (life / 20))
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (255, 255, 255, alpha), (radius, radius), radius)
            self.screen.blit(surface, (x - radius, y - radius))

        # Draw all effects
        for effect in self.blow_effects:
            effect.draw(self.screen)

        # Draw all bubbles
        for bubble in self.bubbles:
            bubble.draw(self.screen)

        # Draw all active messages
        for message in self.messages:
            message.draw(self.screen)

        pygame.display.flip()
        
    def create_bubble_stream(self, x, y, pattern="fountain", count=1):
        if pattern == "fountain":
            # Create a fountain pattern
            for i in range(count):
                angle = math.pi/2 + math.pi/3 * (random.random() - 0.5)  # 60-degree spread
                speed = random.uniform(6, 9)
                bubble = Bubble(x, y, self.screen_width, self.screen_height)
                bubble.dx = math.cos(angle) * speed
                bubble.dy = -math.sin(angle) * speed
                bubble.radius = random.randint(10, 25)
                # Rainbow colors for fountain
                hue = i / count
                rgb = self.hsv_to_rgb(hue, 0.8, 1.0)
                bubble.color = (*rgb, 200)
                self.bubbles.append(bubble)
        elif pattern == "spiral":
            # Create a spiral pattern
            for i in range(count):
                angle = (i / count) * math.pi * 2
                speed = random.uniform(3, 6)
                bubble = Bubble(x, y, self.screen_width, self.screen_height)
                bubble.dx = math.cos(angle) * speed
                bubble.dy = -math.sin(angle) * speed - 2
                bubble.radius = random.randint(8, 20)
                # Color gradient for spiral
                hue = i / count
                rgb = self.hsv_to_rgb(hue, 0.9, 1.0)
                bubble.color = (*rgb, 200)
                self.bubbles.append(bubble)
        elif pattern == "wave":
            # Create a wave pattern
            base_speed = random.uniform(4, 7)
            for i in range(count):
                phase = (i / count) * math.pi * 2
                bubble = Bubble(x, y, self.screen_width, self.screen_height)
                bubble.dx = math.cos(phase) * 3
                bubble.dy = -base_speed
                bubble.radius = random.randint(12, 28)
                # Ocean colors for wave
                rgb = self.hsv_to_rgb(0.5 + random.uniform(-0.1, 0.1), 0.7, 1.0)
                bubble.color = (*rgb, 200)
                self.bubbles.append(bubble)
    
    def hsv_to_rgb(self, h, s, v):
        if s == 0.0:
            return (v, v, v)
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        v = int(v * 255)
        t = int(t * 255)
        p = int(p * 255)
        q = int(q * 255)
        if i == 0: return (v, t, p)
        if i == 1: return (q, v, p)
        if i == 2: return (p, v, t)
        if i == 3: return (p, q, v)
        if i == 4: return (t, p, v)
        if i == 5: return (v, p, q)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.update()
            self.draw()
            clock.tick(60)

        if self.camera_available:
            self.camera.release()
        pygame.quit()

if __name__ == "__main__":
    game = BubbleGame()
    game.run()
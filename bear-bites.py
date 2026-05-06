# Dania Aslam
# Bear Bites!
# Midterm Game, more info in README

# imports
import pygame
import random
import sys
import asyncio

# initialize pygame
pygame.init()

# screen setup
WIDTH = 360
HEIGHT = 640
FPS = 60

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bear Bites!")
CLOCK = pygame.time.Clock()

# colors
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
LIGHT_GRAY = (220, 220, 220)
GRAY = (95, 95, 95)
GOLD = (255, 215, 0)

BUTTON_BLUE = (80, 150, 220)
BUTTON_BLUE_HOVER = (105, 170, 235)
BUTTON_GREEN = (90, 175, 110)
BUTTON_GREEN_HOVER = (110, 195, 130)
BUTTON_RED = (210, 90, 90)
BUTTON_RED_HOVER = (225, 110, 110)

DARK_BG = (24, 24, 40)
CARD_GREEN = (222, 230, 222)
CARD_GREEN_HOVER = (230, 238, 230)
CARD_BLUE = (224, 232, 242)
CARD_BLUE_HOVER = (232, 238, 246)

# fonts
TITLE_FONT = pygame.font.SysFont("impact", 50, bold=False)
SUBTITLE_FONT = pygame.font.SysFont("segoeui", 20, bold=True)
TEXT_FONT = pygame.font.SysFont("segoeui", 16, bold=True)
SMALL_FONT = pygame.font.SysFont("segoeui", 14, bold=True)
BIG_FONT = pygame.font.SysFont("segoeui", 26, bold=True)
COUNTDOWN_FONT = pygame.font.SysFont("impact", 72, bold=False)

# helper functions
def draw_text(surface, text, font, color, x, y, center=False):
    # draws text on screen
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    surface.blit(text_surface, rect)


def safe_random_x(obj_width):
    # generate random X position for falling bites
    return random.randint(10, WIDTH - obj_width - 10)


def clamp(value, minimum, maximum):
    # keeps values within screen bounds
    return max(minimum, min(value, maximum))


def load_and_scale_image(filename, size):
    # loads images & scales
    try:
        image = pygame.image.load(filename).convert_alpha()
        return pygame.transform.smoothscale(image, size)
    except pygame.error:
        return None
    except FileNotFoundError:
        return None


def load_background_cover(filename):
    # load & crop background to fit screen (prevents image from stretching)
    try:
        image = pygame.image.load(filename).convert()
        img_w, img_h = image.get_size()

        # scale to fit screen height
        scale = HEIGHT / img_h
        new_w = int(img_w * scale)
        new_h = HEIGHT

        scaled = pygame.transform.smoothscale(image, (new_w, new_h))

        # center crop
        x = max(0, (new_w - WIDTH) // 2)
        cropped = scaled.subsurface((x, 0, WIDTH, HEIGHT)).copy()

        return cropped

    except pygame.error:
        return None
    except FileNotFoundError:
        return None


# image uploads
# player images
PANDA_IMAGE = load_and_scale_image("panda.png", (90, 90))
POLAR_IMAGE = load_and_scale_image("polar-bear.png", (100, 100))

# falling bites images
BAMBOO_IMAGE = load_and_scale_image("bamboo.png", (50, 50))
FISH_IMAGE = load_and_scale_image("fish.png", (70, 70))

# background images
FOREST_BG = load_background_cover("forest.jpg")
ARCTIC_BG = load_background_cover("arctic.jpg")

# button class
class Button:
    def __init__(self, rect, text, color, hover):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover = hover

    def draw(self, surface):
        # hover effect
        mouse = pygame.mouse.get_pos()
        current_color = self.hover if self.rect.collidepoint(mouse) else self.color

        pygame.draw.rect(surface, current_color, self.rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=12)

        draw_text(
            surface,
            self.text,
            SUBTITLE_FONT,
            WHITE,
            self.rect.centerx,
            self.rect.centery,
            center=True
        )

    def is_clicked(self, event):
        # return true if button is clicked
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# player class
class Player:
    # panda or polar bear
    def __init__(self, bear):
        self.bear_type = bear
        self.width = 90
        self.height = 90
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 120
        self.speed = 6
        self.lives = 3
        self.score = 0

        # rectangle used for collision detection
        self.rect = pygame.Rect(self.x + 15, self.y + 15, self.width - 30, self.height - 30)

    def move(self, keys):
        # move left & right with arrow keys
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed

        self.x = clamp(self.x, 0, WIDTH - self.width)
        self.rect.x = self.x + 15
        self.rect.y = self.y + 15

    def draw(self, surface):
        # draw bear image
        if self.bear_type == "panda" and PANDA_IMAGE:
            surface.blit(PANDA_IMAGE, (self.x, self.y))
        elif self.bear_type == "polar" and POLAR_IMAGE:
            surface.blit(POLAR_IMAGE, (self.x, self.y))
        else:
            pygame.draw.rect(surface, BLACK, self.rect, border_radius=10)

    def get_target_item(self):
        # return correct item based on chosen bear
        return "bamboo" if self.bear_type == "panda" else "fish"


# falling items
class FallingItem:
    # bamboo or fish
    def __init__(self, item_type, speed):
        self.item_type = item_type

        # different hitbox sizes for bamboo and fish
        if self.item_type == "fish":
            self.width = 70
            self.height = 70
        else:
            self.width = 50
            self.height = 50

        self.x = safe_random_x(self.width)
        self.y = random.randint(-700, -40)
        self.speed = speed

        # rectangle used for collision detection
        self.rect = pygame.Rect(self.x + 10, self.y + 10, self.width - 20, self.height - 20)

    def update(self):
        # move item down
        self.y += self.speed
        self.rect.x = self.x + 10
        self.rect.y = self.y + 10

    def reset(self, speed):
        # respawn object above screen
        self.x = safe_random_x(self.width)
        self.y = random.randint(-400, -40)
        self.speed = speed
        self.rect.x = self.x
        self.rect.y = self.y

    def draw(self, surface):
        # draw bite image
        if self.item_type == "bamboo" and BAMBOO_IMAGE:
            surface.blit(BAMBOO_IMAGE, (self.x, self.y))
        elif self.item_type == "fish" and FISH_IMAGE:
            surface.blit(FISH_IMAGE, (self.x, self.y))
        else:
            pygame.draw.rect(surface, LIGHT_GRAY, self.rect, border_radius=8)


# background & ui
def draw_bg(surface, bear):
    # draw background depending on bear
    if bear == "panda" and FOREST_BG:
        surface.blit(FOREST_BG, (0, 0))
    elif bear == "polar" and ARCTIC_BG:
        surface.blit(ARCTIC_BG, (0, 0))
    else:
        surface.fill((230, 230, 230))


def draw_ui(surface, player, time_left):
    # draw ui bar with score, lives, time
    panel = pygame.Rect(10, 10, WIDTH - 20, 60)

    panel_surface = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)

    # slightly transparent
    pygame.draw.rect(
        panel_surface,
        (245, 245, 245, 220),
        (0, 0, panel.width, panel.height),
        border_radius=18
    )

    surface.blit(panel_surface, (panel.x, panel.y))

    # section positions
    score_x = WIDTH * 0.2
    lives_x = WIDTH * 0.5
    time_x = WIDTH * 0.8

    # labels
    draw_text(surface, "Score", SMALL_FONT, GRAY, score_x, 20, center=True)
    draw_text(surface, "Lives", SMALL_FONT, GRAY, lives_x, 20, center=True)
    draw_text(surface, "Time", SMALL_FONT, GRAY, time_x, 20, center=True)

    # values
    draw_text(surface, str(player.score), SUBTITLE_FONT, BLACK, score_x, 42, center=True)
    draw_text(surface, str(player.lives), SUBTITLE_FONT, BLACK, lives_x, 42, center=True)

    # timer turns red in final 10 seconds
    time_color = (200, 50, 50) if time_left <= 10 else BLACK
    draw_text(surface, str(time_left), SUBTITLE_FONT, time_color, time_x, 42, center=True)


# character select screen
def character_select():
    # display bears with clickable cards
    panda_card = pygame.Rect(30, 225, 130, 210)
    polar_card = pygame.Rect(200, 225, 130, 210)

    while True:
        SCREEN.fill(DARK_BG)

        # title
        draw_text(SCREEN, "Bear Bites!", TITLE_FONT, WHITE, WIDTH // 2, 100, center=True)
        draw_text(SCREEN, "Choose your bear!", TEXT_FONT, (190, 190, 200), WIDTH // 2, 175, center=True)

        mouse_pos = pygame.mouse.get_pos()

        # hover colors
        panda_fill = CARD_GREEN_HOVER if panda_card.collidepoint(mouse_pos) else CARD_GREEN
        polar_fill = CARD_BLUE_HOVER if polar_card.collidepoint(mouse_pos) else CARD_BLUE

        # draw cards
        pygame.draw.rect(SCREEN, panda_fill, panda_card, border_radius=20)
        pygame.draw.rect(SCREEN, WHITE, panda_card, 2, border_radius=20)

        pygame.draw.rect(SCREEN, polar_fill, polar_card, border_radius=20)
        pygame.draw.rect(SCREEN, WHITE, polar_card, 2, border_radius=20)

        # panda image
        if PANDA_IMAGE:
            panda_x = panda_card.centerx - PANDA_IMAGE.get_width() // 2
            panda_y = panda_card.y + 35
            SCREEN.blit(PANDA_IMAGE, (panda_x, panda_y))

        # polar image
        if POLAR_IMAGE:
            polar_x = polar_card.centerx - POLAR_IMAGE.get_width() // 2
            polar_y = polar_card.y + 35
            SCREEN.blit(POLAR_IMAGE, (polar_x, polar_y))

        # names only
        draw_text(SCREEN, "Panda", SUBTITLE_FONT, BLACK, panda_card.centerx, panda_card.y + 150, center=True)
        draw_text(SCREEN, "Polar", SUBTITLE_FONT, BLACK, polar_card.centerx, polar_card.y + 150, center=True)

        # small instruction
        draw_text(SCREEN, "Tap a bear to start", SMALL_FONT, (170, 170, 185), WIDTH // 2, 500, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if panda_card.collidepoint(event.pos):
                    return "panda"
                if polar_card.collidepoint(event.pos):
                    return "polar"

        pygame.display.flip()
        CLOCK.tick(FPS)


# countdown & rule screen
def show_countdown_screen(bear_type):
    # 5 second countdown & game rules
    start_ticks = pygame.time.get_ticks()
    countdown_time = 5

    if bear_type == "panda":
        title = "Panda Mode"
        rule_1 = "Catch as much bamboo as you can!"
        rule_2 = "Avoid catching fish."
        rule_3 = "You have 3 lives."
        rule_4 = "Bites fall faster as time runs out!"
        accent_color = BUTTON_GREEN
    else:
        title = "Polar Mode"
        rule_1 = "Catch as many fish as you can!"
        rule_2 = "Avoid catching bamboo."
        rule_3 = "You have 3 lives."
        rule_4 = "Bites fall faster as time runs out!"
        accent_color = BUTTON_BLUE

    while True:
        CLOCK.tick(FPS)

        elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = max(0, countdown_time - elapsed)

        # background based on bear
        draw_bg(SCREEN, bear_type)

        # text overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 185))
        SCREEN.blit(overlay, (0, 0))

        # instruction card
        card = pygame.Rect(22, 105, WIDTH - 44, 355)
        pygame.draw.rect(SCREEN, WHITE, card, border_radius=24)
        pygame.draw.rect(SCREEN, LIGHT_GRAY, card, 2, border_radius=24)

        # title & countdown
        draw_text(SCREEN, title, BIG_FONT, BLACK, WIDTH // 2, 150, center=True)
        draw_text(SCREEN, str(time_left), COUNTDOWN_FONT, accent_color, WIDTH // 2, 225, center=True)

        # rules
        draw_text(SCREEN, rule_1, TEXT_FONT, BLACK, WIDTH // 2, 290, center=True)
        draw_text(SCREEN, rule_2, TEXT_FONT, BLACK, WIDTH // 2, 325, center=True)
        draw_text(SCREEN, rule_3, TEXT_FONT, BLACK, WIDTH // 2, 360, center=True)
        draw_text(SCREEN, rule_4, TEXT_FONT, BLACK, WIDTH // 2, 395, center=True)

        # get ready message
        draw_text(SCREEN, "Get ready!", SMALL_FONT, GRAY, WIDTH // 2, 435, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()

        if time_left <= 0:
            return


# end screen
def end_screen(player, won):
    # display game over screen with final score & play again / quit buttons
    again_btn = Button((55, 500, 110, 48), "Play Again", BUTTON_GREEN, BUTTON_GREEN_HOVER)
    quit_btn = Button((195, 500, 110, 48), "Quit", BUTTON_RED, BUTTON_RED_HOVER)

    while True:
        draw_bg(SCREEN, player.bear_type)

        # overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 120))
        SCREEN.blit(overlay, (0, 0))

        # center the result card
        pygame.draw.rect(SCREEN, (255, 255, 255), (30, 155, 300, 240), border_radius=22)
        pygame.draw.rect(SCREEN, LIGHT_GRAY, (30, 155, 300, 240), 2, border_radius=22)

        title = "You Win!" if won else "Game Over!"
        subtitle = "Great job feeding the bear!" if won else "You ran out of lives."

        draw_text(SCREEN, title, TITLE_FONT, BLACK, WIDTH // 2, 240, center=True)
        draw_text(SCREEN, subtitle, TEXT_FONT, GRAY, WIDTH // 2, 300, center=True)
        draw_text(SCREEN, f"Score: {player.score}", BIG_FONT, GOLD, WIDTH // 2, 330, center=True)

        again_btn.draw(SCREEN)
        quit_btn.draw(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if again_btn.is_clicked(event):
                return True

            if quit_btn.is_clicked(event):
                return False

        pygame.display.flip()
        CLOCK.tick(FPS)


# main game loop
async def run():
    # run game
    selected_bear = character_select()

    # show rules & countdown
    show_countdown_screen(selected_bear)

    player = Player(selected_bear)

    # create falling bites
    items = [FallingItem("bamboo", 4) for _ in range(3)] + \
            [FallingItem("fish", 4) for _ in range(3)]

    game_time = 30
    start = pygame.time.get_ticks()

    while True:
        CLOCK.tick(FPS)

        # timer
        elapsed = (pygame.time.get_ticks() - start) // 1000
        time_left = max(0, game_time - elapsed)

        # difficulty increases over time
        progress = (game_time - time_left) / game_time
        speed = 4 + int(progress * 6)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # player movement
        keys = pygame.key.get_pressed()
        player.move(keys)

        # draw background & ui
        draw_bg(SCREEN, player.bear_type)
        draw_ui(SCREEN, player, time_left)

        # update, draw, & check collisions
        for item in items:
            item.speed = speed + random.randint(0, 1)
            item.update()

            if item.y > HEIGHT:
                item.reset(speed)

            # collision detection
            if player.rect.colliderect(item.rect):
                if item.item_type == player.get_target_item():
                    player.score += 1
                else:
                    player.lives -= 1

                item.reset(speed)

            item.draw(SCREEN)

        player.draw(SCREEN)

        pygame.display.flip()

        # end conditions
        if player.lives <= 0:
            return end_screen(player, won=False)

        if time_left <= 0:
            return end_screen(player, won=True)


# start game
async def main():
    # can replay game
    while True:
        play_again = await run()
        if not play_again:
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    # main()
    asyncio.run(main())
import pygame as pg
import random
import os
import time

WIDTH = 480
HEIGHT = 600
FPS = 60
LIVES = 3
POINTS_FOR_NEW_MOB = 150

#define colors
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)

pg.init()
pg.mixer.init()
screen = pg.display.set_mode((WIDTH,HEIGHT))

all_sprites = pg.sprite.Group()
mobs = pg.sprite.Group()
bullets = pg.sprite.Group()
powerups = pg.sprite.Group()
menu_sprites = pg.sprite.Group()

font_name = pg.font.match_font("arial")

def draw_text(surf,text,font_size,pos):
    font = pg.font.Font(font_name, font_size)
    text = font.render(text, True, WHITE)
    textpos = text.get_rect(center=pos)  # topright=(WIDTH-30,30)
    surf.blit(text, textpos)

def draw_shield_bar(surf,pos,val):
    if val < 0:
        val = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (val/100)*BAR_LENGTH
    outline_rect = pg.Rect(pos[0],pos[1],BAR_LENGTH,BAR_HEIGHT)
    fill_rect = pg.Rect(pos[0],pos[1],fill,BAR_HEIGHT)
    pg.draw.rect(surf,WHITE, outline_rect,2)
    pg.draw.rect(surf,GREEN, fill_rect)

def draw_lives (surf,pos,lives,img):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = pos[0] + 30*i
        img_rect.y = pos[1]
        surf.blit(img,img_rect)



# set up assets folders
#game_folder = os.path.dirname(__file__)

def load_image(name,size=None):
    fullname = os.path.join("data",name)
    image = pg.image.load(fullname)
    if size:
        image = pg.transform.scale(image,size)
    if ".png" in name:
        image = image.convert_alpha()
    else:
        image = image.convert()
    return image

def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pg.mixer:
        return NoneSound()
    fullname = os.path.join('data', name)
    try:
        sound = pg.mixer.Sound(fullname)
    except pg.error as message:
        print('Cannot load sound:', fullname)
        raise SystemExit(message)
    return sound

#sounds
shoot_sound = load_sound("shoot.wav")
shoot_sound.set_volume(0.3)
explosion_sound = load_sound("explosion.wav")
gameover_sound = load_sound("gameover.wav")
gameover_sound.set_volume(0.3)
meteor_explosion = load_sound("meteorExplosion.wav")
meteor_explosion.set_volume(0.3)
pickup_sound = load_sound("pickup.wav")

#img
explosion_anim = {}
explosion_anim["regular"] = []
explosion_anim["sonic"] = []

for i in range(9):
    explosion_anim["regular"].append(load_image("regularExplosion0"+str(i)+".png"))
    explosion_anim["sonic"].append(load_image("sonicExplosion0"+str(i)+".png"))

player_mini = load_image("ship.png",(25,19))
powerup_images = {}
pw_up_size = (18,23)
powerup_images["shield"] = load_image("shield.png",pw_up_size)
powerup_images["bolt"] = load_image("bolt.png",pw_up_size)

class Player(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        im_w = 70
        im_h = 50
        self.image = load_image("ship.png",(im_w,im_h))
        self.rect = self.image.get_rect()
        self.radius = im_w/2 if im_w < im_h else im_h/2
        #pg.draw.circle(self.image,RED,self.rect.center,self.radius)
        self.rect.centerx = WIDTH/2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0
        self.shield = 100
        self.shoot_delay = 350
        self.last_shoot = pg.time.get_ticks()
        self.lives = LIVES
        self.hidden = False
        self.hide_timer = pg.time.get_ticks()
        self.isBolt = False
        self.bolt_time = 5000
        self.bolt_start = None
        self.bolt_enforce = 250

    def update(self):
        now = pg.time.get_ticks()
        if self.isBolt:
            if now - self.bolt_start > self.bolt_time:
                self.isBolt = False
                self.shoot_delay += self.bolt_enforce

        if self.hidden and now - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH/2
            self.rect.bottom = HEIGHT-10
        self.speedx = 0
        keystate = pg.key.get_pressed()
        if keystate[pg.K_LEFT]:
            self.speedx = -5
        if keystate[pg.K_RIGHT]:
            self.speedx = 5
        if keystate[pg.K_SPACE]:
            self.shoot()
        self.rect.x += self.speedx
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        elif self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        now = pg.time.get_ticks()
        if now - self.shoot_delay >= self.last_shoot:
            self.last_shoot = now
            shoot_sound.play()
            b = Bullet(self.rect.centerx,self.rect.top)
            all_sprites.add(b)
            bullets.add(b)

    def hide(self):
        self.hidden = True
        self.hide_timer = pg.time.get_ticks()
        self.rect.center = (WIDTH/2, HEIGHT+200)

    def bolt_powerup(self):
        self.bolt_start = pg.time.get_ticks()
        if not self.isBolt:
            self.isBolt = True
            self.shoot_delay -= self.bolt_enforce


class Mob(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        im_w = random.randint(40,90)
        im_h = im_w

        self.image = load_image("asteroid"+str(random.randint(1,6))+".png",(im_w,im_h))
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.radius = (im_w / 2 if im_w < im_h else im_h / 2)*.85
        #pg.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150,-100)
        self.speedy = random.randrange(1,8)
        self.speedx = random.randrange(-3,3)
        self.angle = 0


    def update(self):
        delta_a = self.speedx*self.speedy
        if self.angle + delta_a > 360:
            self.angle = self.angle+delta_a-360
        elif self.angle + delta_a < 0:
            self.angle = 360 + self.angle + delta_a
        else:
            self.angle+=delta_a
        center = self.rect.center
        self.image = pg.transform.rotate(self.original_image,self.angle)
        self.rect = self.image.get_rect(center=center)
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT + 20 or self.rect.left < -100 or self.rect.right > WIDTH + 100:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)
            self.speedx = random.randrange(-3, 3)

class Bullet(pg.sprite.Sprite):
    def __init__(self,x,y):
        pg.sprite.Sprite.__init__(self)
        self.image = load_image("bullet.png",(10,20))
        self.rect = self.image.get_rect()
        # pg.draw.rect(self.image, GREEN, self.rect)
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        #kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()

class Pow(pg.sprite.Sprite):
    def __init__(self,center):
        pg.sprite.Sprite.__init__(self)
        self.type = random.choice(["shield","bolt"])
        self.image = powerup_images[self.type]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 2

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

class Explosion(pg.sprite.Sprite):
    def __init__(self, type, center, rad):
        pg.sprite.Sprite.__init__(self)
        self.frame = 0
        self.rad = rad
        self.type = type
        self.image = pg.transform.scale(explosion_anim[self.type][self.frame],(self.rad*2,self.rad*2))
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.last_update = pg.time.get_ticks()
        self.frame_rate = 75

    def update(self):
        if self.frame == len(explosion_anim[self.type]):
            self.kill()
        elif self.frame < len(explosion_anim[self.type]):
            now = pg.time.get_ticks()
            if now - self.last_update >= self.frame_rate:
                self.image = pg.transform.scale(explosion_anim[self.type][self.frame],(self.rad*2,self.rad*2))
                #self.image = explosion_anim["a"][self.frame]
                self.frame += 1
                self.last_update = now

cursor_size = (30,30)
cursors_img = {"flat":load_image("flat_cursor.png",cursor_size),"hand":load_image("hand_cursor.png",cursor_size)}

class Mouse(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.type = "flat"
        self.image = cursors_img[self.type]
        self.rect = self.image.get_rect()
        pos = pg.mouse.get_pos()
        if self.type == "flat":
            self.rect.topleft = pos
        elif self.type == "hand":
            self.rect.x = pos[0] - int(self.rect.width / 3)
            self.rect.y = pos[1]

    def update(self):
        pos = pg.mouse.get_pos()
        if pg.mouse.get_focused() == 0:
            self.rect.topleft = (WIDTH + 100, HEIGHT + 100)
            return
        if self.type == 'flat':
            self.rect.topleft = pos
        elif self.type == 'hand':
            self.rect.x = pos[0] - int(self.rect.width/3)
            self.rect.y = pos[1]

    def set_type(self,type):
        self.type = type
        self.image = cursors_img[self.type]

btn_size = (100,100)
buttons = {}
buttons['again'] = [load_image("againUnpressed.png",btn_size),load_image('againPressed.png',btn_size)]
buttons['close'] = [load_image("closeUnpressed.png",btn_size),load_image('closePressed.png',btn_size)]

class Button(pg.sprite.Sprite):
    def __init__(self,type,pos):
        pg.sprite.Sprite.__init__(self)
        self.type = type
        self.image = buttons[self.type][0]
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.isHovered = False

    def update(self):
        pos = pg.mouse.get_pos()
        if self.rect.x <= pos[0] <= self.rect.topright[0] and self.rect.y <= pos[1] <= self.rect.midbottom[1]:
            self.image = buttons[self.type][1]
            self.isHovered = True
        else:
            self.image = buttons[self.type][0]
            self.isHovered = False

    def click(self):
        if self.isHovered:
            return True





def spawn_mob():
    m = Mob()
    all_sprites.add(m)
    mobs.add(m)



def main():
    #initialize pygame and create window
    pg.display.set_caption("Shmup")
    pg.mouse.set_visible(False)
    clock = pg.time.Clock()
    pg.mixer.music.load(os.path.join("data","backsong.mp3"))
    pg.mixer.music.play(loops=-1)

    # explosions_img = []
    # for i in range(9):
    #     explosions_img.append(load_image("regularExplosion0"+str(i)+".png"))


    #game graphics
    back_img = load_image("starfield.png",(WIDTH,HEIGHT))
    back_img_rect = back_img.get_rect()

    player = Player()

    all_sprites.add(player)
    mobs_num = 10

    for i in range(mobs_num):
        spawn_mob()

    additional_mobs = 0
    #Game Loop
    running = True
    points_counter = 0

    gap = 20
    btn_close = Button("close", ((WIDTH - (btn_size[0]*2) - gap)/2+btn_size[0]+gap, HEIGHT/2-30))
    btn_again = Button("again", ((WIDTH - (btn_size[0]*2) - gap)/2, HEIGHT/2-30))
    mouse = Mouse()
    menu_sprites.add(btn_close)
    menu_sprites.add(btn_again)
    menu_sprites.add(mouse)





    while running:

        # keep loop running at the right speed
        clock.tick(FPS)

        #Process input (events)
        for event in pg.event.get():
            #check for closing window
            if event.type == pg.QUIT:
                running = False

        #Update
        all_sprites.update()

        #check to see if a  bullet hit a mob
        hits = pg.sprite.groupcollide(mobs,bullets,True,True)
        for hit in hits:

            points_counter+= int(hit.radius - 10)
            all_sprites.add(Explosion("regular",hit.rect.center,int(hit.radius)-1))
            meteor_explosion.play()
            if random.random() > .9:
                pow = Pow(hit.rect.center)
                all_sprites.add(pow)
                powerups.add(pow)
            spawn_mob()
        #check to see if a mob hit the player
        hits = pg.sprite.spritecollide(player,mobs, True, pg.sprite.collide_circle)
        for hit in hits:
            player.shield -= hit.radius
            explosion_sound.play()
            all_sprites.add(Explosion("regular",hit.rect.center, 16))
            spawn_mob()
            if player.shield <= 0:
                death_explosion = Explosion("sonic", player.rect.center, int(player.rect.height*3))
                all_sprites.add(death_explosion)
                player.hide()
                player.lives -= 1
                player.shield = 100

        hits = pg.sprite.spritecollide(player,powerups,True)
        for hit in hits:
            pickup_sound.play()
            if hit.type == "shield":
                player.shield += random.randrange(10,30)
                if player.shield > 100:
                    player.shield = 100
            if hit.type == "bolt":
                player.bolt_powerup()
        #if the player died and the explosion has finished playing
        if player.lives == 0 and not death_explosion.alive():
            gameover_sound.play()
            sub_running = True
            while sub_running:
                for event in pg.event.get():
                    if btn_close.isHovered or btn_again.isHovered:
                        mouse.set_type("hand")
                    else:
                        mouse.set_type("flat")

                    if event.type == pg.QUIT:
                        sub_running = False
                        running = False
                    elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_again.click():
                            player.lives = LIVES
                            sub_running = False
                            points_counter = 0
                            for spr in all_sprites:
                                if type(spr).__name__ in ("Mob","Bullet","Pow","Explosion"):
                                    spr.kill()
                            for i in range(mobs_num):
                                spawn_mob()
                            additional_mobs = 0
                        elif btn_close.click():
                            sub_running = False
                            running = False




                menu_sprites.update()
                screen.blit(back_img, back_img_rect)
                draw_text(screen, "Your score: " + str(points_counter), 36, (WIDTH / 2, HEIGHT / 2 - 80))
                menu_sprites.draw(screen)
                pg.display.flip()
            continue


        if additional_mobs < 80 and int(points_counter/POINTS_FOR_NEW_MOB) > additional_mobs:
            num_of_new = int(points_counter/100)-additional_mobs
            additional_mobs += num_of_new
            for i in range(num_of_new):
                spawn_mob()

        #Draw/render
        screen.blit(back_img,back_img_rect)
        all_sprites.draw(screen)
        draw_text(screen,str(points_counter),36,(WIDTH/2,30))
        if running:
            draw_shield_bar(screen,(5,5),player.shield)
            draw_lives(screen, (5, 20), player.lives, player_mini)


        # *after* drawing everything, flip the display
        pg.display.flip()
    pg.mixer.music.fadeout(1)
    pg.quit()

if __name__ == '__main__':
    main()




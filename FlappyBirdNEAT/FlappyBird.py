import pygame
import random
import os
import time
import neat
import visualize
import pickle
pygame.font.init()  # init font


#Defining all constants 
WIDTH = 600
HEIGHT = 800
FLOOR = 730
FONT1 = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")


#Loading the images using py game 
pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
background_image = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

gen = 0

class Bird:
    MAX_ROTATION = 25   #-->tilt angle max 
    ROT_VEL = 20        #-->Max rotation per frame
    ANIMATION_TIME = 5  #-->Max time to shoe animation
    IMGS = bird_images


    def __init__(self, x, y):
        # :param x: starting x pos (int)
        # :param y: starting y pos (int)
        # :return: None

        self.x = x
        self.y = y
        self.tilt = 0         # degrees to tilt
        self.tick_count = 0   # For falling and moving upward
        self.vel = 0
        self.height = self.y
        self.img_count = 0    # Which bird image
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5       #Moving upward is negative velocity --> Jumps
        self.tick_count = 0    #Keeps track of when we last jumped 
        self.height = self.y   #Original starting point 
    

    # While true : 
    #     bird.move()
    
    #Dint have to tack care of in original code 
    def move(self):
        # Increment the tick count to represent the passage of time
        self.tick_count += 1
        
        # Calculate the displacement based on initial velocity and acceleration
        displacement = self.vel * self.tick_count  # Linear displacement
        displacement += 0.5 * 3 * (self.tick_count) ** 2  # Add parabolic displacement (acceleration term)
        
        # Cap the displacement to a terminal velocity of 15 units --> trial and erros
        if displacement >= 15:
            displacement = (displacement / abs(displacement)) * 15
        
        # Apply an additional downward displacement if moving upwards
        if displacement < 0: displacement -= 2
        
        # Update the vertical position based on displacement
        self.y = self.y + displacement
        
        # Adjust the tilt of the object based on its movement
        if displacement < 0 or self.y < self.height + 50:  # Tilt up if moving upwards or below a certain height 
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION 
        else:  # Tilt down if moving downwards
            if self.tilt > -90:  
                self.tilt -= self.ROT_VEL    #rotate doqn --> nose diving illusion 
    def rotate_func(self, surf, image, x, y, angle):
        # Rotate the image around its center
        rotated_image = pygame.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=(x, y)).center)
        surf.blit(rotated_image, new_rect.topleft)
    def draw(self, win):
        # Increment the image count to keep track of animation progress
        self.img_count += 1

        #which image to show based on the animation time --> flap wings
        if self.img_count <= self.ANIMATION_TIME:
            # Display the first image
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            # Display the second image 
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            # Display the third image
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            # Display the second image again 
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            # Reset to the first image after a full cycle of animation
            self.img = self.IMGS[0]
            # Reset image count to start the animation loop again
            self.img_count = 0

        # Prevent the bird from flapping its wings when it is nose-diving
        if self.tilt <= -80:
            # Set the image to the second image (usually a neutral pose)
            self.img = self.IMGS[1]
            # Adjust the image count to stop the animation at this frame
            self.img_count = self.ANIMATION_TIME * 2

        # Rotate and draw the bird image on the window at the bird's current position
        self.rotate_func(win, self.img, self.x, self.y, self.tilt)


    def get_mask(self):
        #Collions 
        return pygame.mask.from_surface(self.img)
# def draw_window_for_bird(win,bird):
#     win.blit(background_image , (0,0))
#     bird.draw(win)
#     pygame.display.update()

# def main():
#     bird = Bird(200,200)
#     win = pygame.display.set_mode((WIDTH,HEIGHT))
#     run = True
#     while run:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 run = False
#         draw_window_for_bird(win,bird)
#     pygame.quit()
#     quit()

# main()

class Pipe():
    GAP = 200  #Gao between pipes 
    VELOCITY = 5

    def __init__(self, x):           #y -->random {height random}
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False          #have we passed the pipe or not

        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)                #top of the pipe 
        self.top = self.height - self.PIPE_TOP.get_height()    #can be at negative position 
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VELOCITY        #move pipe to left each second

    def draw(self, win):
        # draw top
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # draw bottom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


    def collide(self, bird, win):
        # mask is the array of pixels inside the box --> more or less the outline of the bird 
        # figures out if each pixel is trasperant or not 
        # and puts the non transparent in the two d array
        # we do this for both bird and pipe --> and check if they collide or not 


        bird_mask = bird.get_mask()
         # Create masks for the top and bottom pipes using their respective images
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Calculate the offset between the bird and the top pipe
        # This is the difference in their x and y coordinates
        #How far they are away from each other 
        top_offset = (self.x - bird.x, self.top - round(bird.y))

        # Calculate the offset between the bird and the bottom pipe
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Check for overlap between the bird's mask and the bottom pipe's mask
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)

        # Check for overlap between the bird's mask and the top pipe's mask
        top_point = bird_mask.overlap(top_mask, top_offset)

        # If there is an overlap with either the top or bottom pipe, return True (collision detected)
        return bottom_point or top_point #--> basic check for colision 

class Base:
    #We need to move base also because the image is not infintly long 
    VELOCITY = 5
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        # two images for base 
        # Both move at the same speed
        # and the first image as soon as it move out of the window goes behind the second image
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))
#Testing 

# def draw_window1(win,bird,pipes,base,score):
#     win.blit(background_image,(0,0))
#     for pipe in pipes : pipe.draw(win)
#     text = FONT1.render("Score : " + str(score),1,(255,255,255))
#     win.blit(text,(WIDTH - 10 - text.get_width(),10))
#     base.draw(win)
#     bird.draw(win)
#     pygame.display.update()

# def main():
#     base = Base(700)
#     pipes = [Pipe(600)]
#     bird = Bird(230,350)
#     win = pygame.display.set_mode((WIDTH,HEIGHT))
#     clock = pygame.time.Clock()
#     score = 0
#     run = True
#     while run :
#         clock.tick(30)
#         for event in pygame.event.get():
#             if(event.type == pygame.QUIT) : run = False
#         rem = []
#         add_pipe = False
#         for pipe in pipes:
#             if(pipe.collide(bird,win)) : pass
#             if pipe.x + pipe.PIPE_TOP.get_width() < 0 :   #when pipe moves out of the screen
#                 rem.append(pipe)

#             if not pipe.passed and pipe.x < bird.x :
#                 pipe.passed = True
#                 add_pipe = True
#             pipe.move() # to actually move the pipe
#         if add_pipe : 
#             score+=1
#             pipes.append(Pipe(600))
#         for r in rem : pipes.remove(r)
#         if bird.y + bird.img.get_height() >= 730 : #hits the ground
#             pass
        
#         base.move() 
#         draw_window1(win,bird,pipes,base,score)

# main()

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    if gen == 0: gen = 1
    win.blit(background_image, (0,0))
    for pipe in pipes: pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # draw bird
        bird.draw(win)

    # score
    score_label = FONT1.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIDTH - score_label.get_width() - 15, 10))

    # generations
    score_label = FONT1.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = FONT1.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    pygame.display.update()

#Fitness fucntion 
def eval_genomes(genomes, config):
    global WIN, gen
    win = WIN
    gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    nets = []
    birds = []
    ge = []
    for _, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # determine whether to use the first or second
                pipe_ind = 1                                                                 # pipe on the screen for neural network input

        for x, bird in enumerate(birds):  # give each bird a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1
            bird.move()

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:  # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                bird.jump()

        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # check for collision
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            # can add this line to give more reward for passing through a pipe (not required)
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        # break if score gets large enough
        '''if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break'''


def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    winner = p.run(eval_genomes, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedForward.txt')
    run(config_path)
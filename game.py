import pygame

pygame.init()

class Game:
    def __init__(self):
        pygame.display.set_caption("ninja game")

        self.screen = pygame.display.set_mode((640, 480))

        self.clock = pygame.time.Clock()

        self.img = pygame.image.load(".venv/include/data/images/clouds/cloud_1.png")


    def run(self):
        while True:
            self.screen.blit(self.img, (100, 200))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()


            pygame.display.update()
            self.clock.tick(60)

Game().run()
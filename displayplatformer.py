import pygame
from networking import NetworkGame
import world as wd
import engine as eng
import json
import ipdb
import os
import random
# os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

FPS = pygame.time.Clock()


class ClientPlatformer(NetworkGame):
  def __init__(self, tile, window_coordinates=None):
    """Sets up all the needed client settings"""
    super().__init__(tile)
    if window_coordinates:
      # passed in the location for the window to be at. Used for debugging
      os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (window_coordinates[0], window_coordinates[1])
    pygame.init()
    self.load_time = .01

    self.engine = eng.Engine()
    self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT) )
    self.game_objects = {}
    # self.background = pygame.image.load("assets/background" + str(self.tile[0]) + str(self.tile[1]) + ".png")
    self.background = pygame.image.load("assets/backgroun.png")
    self.background_rect = self.background.get_rect()

  def init_game(self, data):
    """Get the initial configuration of the game from the master node."""
    for game_obj in data['game_obj']:
      constructor = getattr(wd, game_obj['constructor'])
      translate_pos = self.translate_to_local((game_obj['rect'][0], game_obj['rect'][1]))
      # TODO: Send Spritesheet also
      if translate_pos != 0:
        self.game_objects[game_obj['id']] = constructor(translate_pos[0], translate_pos[1],
                                                        game_obj['rect'][2], game_obj['rect'][3],
                                                        sprite_sheet=game_obj['sprite_sheet'], obj_id=game_obj['id'])
      else:
        self.game_objects[game_obj['id']] = constructor(game_obj['rect'][0], game_obj['rect'][1],
                                                        game_obj['rect'][2], game_obj['rect'][3],
                                                        sprite_sheet=game_obj['sprite_sheet'], obj_id=game_obj['id'])

        self.game_objects[game_obj['id']].render = False

    self.clear_rects = []
    return data

  def update(self, data):
    """override this method, only hook needed for the server
    :param data: A python dict with data passed from the server
    :type data: dict"""
    if data['state'] == 'play':
      return self.play_state(data)
    elif data['state'] == 'load':
      return self.load_state(data)
    else:
      ipdb.set_trace()

  def clear(self, rects=[]):
    """clear where the previous game objects were + whatever rects are specified
    in the passed in rect(good for timers and debug messages"""
    for game_obj in self.game_objects.values():
      if game_obj.render == True and isinstance(game_obj, wd.MovableGameObject):
        self.window.blit(self.background, (game_obj.rect.x, game_obj.rect.y), game_obj.rect)
    for rect in rects:
      self.window.blit(self.background, (rect.x, rect.y), rect)
        # self.window.blit(self.background, self.background_rect)
        # self.window.fill(color)

  def clear_entire_screen(self):
    self.window.blit(self.background, self.background_rect)

  def load_state(self, data):
    """Fires off a load animation for every game object that is on this nodes screen
    :param data: TODO: make this fire off a specific load animation
    :type data: dict"""
    self.clear_entire_screen()
    obj_on_screen = [game_obj for game_obj in self.game_objects.values() if game_obj.render]
    self.engine.load_animation(obj_on_screen, self.background, self.window)
    update_rects = []
    for obj_id, game_obj in self.game_objects.items():
      if isinstance(game_obj, wd.SimpleScenery):
        game_obj.draw(self.window)
        game_obj.dirt_sprite = False  # DOn't draw again unless it moves
        update_rects.append(game_obj.rect)
    pygame.display.update(update_rects)
    return {'state': 'play'}

  def play_state(self, data):
    """the main loop of the game. Takes the python dict and checks if the game 
    object is in the nodes area. If so it sets it to render
    :para data: python dict with various game object packets
    :type data: dict"""
    self.clear(self.clear_rects)
    self.clear_rects = []
    for obj_id in data['deleted_objs']:
      del self.game_objects[obj_id]
    for game_obj in data['added_objs']:
      constructor = getattr(wd, game_obj['constructor'])
      self.game_objects[game_obj['id']] = constructor(game_obj['rect'][0], game_obj['rect'][1],
                                                      game_obj['rect'][2], game_obj['rect'][3],
                                                      sprite_sheet=game_obj['sprite_sheet'], obj_id=game_obj['id'])

      self.game_objects[game_obj['id']].render = False

    for packet in data['game_objects']:
      translated_pos = self.translate_to_local((packet['rect'].x, packet['rect'].y))
      if translated_pos != 0:
        # TODO: don't translate here, do it in a better place
        packet['rect'].x, packet['rect'].y = translated_pos
        self.game_objects[packet['id']].read_packet(packet)
      else:
        self.game_objects[packet['id']].render = False

    # TODO: this is what loop over game dict is for
    update_rects = []
    for obj_id, game_obj in self.game_objects.items():
      if game_obj.render:
        clear_rect = game_obj.draw(self.window)
        if game_obj.dirt_sprite:
          update_rects.append(game_obj.rect)
        if clear_rect:
          self.clear_rects.append(clear_rect)
    print(len(update_rects))
    print(update_rects)
    pygame.display.update(update_rects)
    #pygame.display.flip()

    data_struct = {'state': 'play'}
    return data_struct

  def translate_to_local(self, pos):
    """translates the given data to the local node. Wrapper for call to game
    :param pos: a tuple of an x and y coordinate
    :type pos: tuple
    :rtype: int or tuple
    """
    if ((self.tile[0] + 1) * SCREEN_WIDTH > pos[0] >= self.tile[0] * SCREEN_WIDTH and
                (self.tile[1] + 1) * SCREEN_HEIGHT > pos[1] >= self.tile[1] * SCREEN_HEIGHT):
      translated_pos = [pos[0] - self.tile[0] * SCREEN_WIDTH,
                        (self.tile[1]) * SCREEN_HEIGHT + pos[1]]
    else:
      translated_pos = 0
    return translated_pos  # , translated_pos_2)

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    pass


import pygame
from networking import NetworkGame
import world as wd
import engine as eng
import json
# import ipdb

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600


class ClientPlatformer(NetworkGame):
  def __init__(self, tile):
    """Sets up all the needed client settings"""
    super(ClientPlatformer, self).__init__(tile)
    pygame.init()
    self.load_time = .01

    self.engine = eng.Engine()
    self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.game_objects = {}

  def init_game(self, data):
    """Get the initial configuration of the game from the master node."""
    for obj_type, obj_list in data.items():
      for game_obj in obj_list:
        constructor = getattr(wd, game_obj['constructor'])
        translate_pos = self.translate_to_local((game_obj['rect'][0], game_obj['rect'][1]))
        if translate_pos != 0:
          self.game_objects[game_obj['id']] = constructor(translate_pos[0], translate_pos[1],
                                                          game_obj['rect'][2], game_obj['rect'][3],
                                                          color=game_obj['color'], obj_id=game_obj['id'])
        else:
          self.game_objects[game_obj['id']] = constructor(game_obj['rect'][0], game_obj['rect'][1],
                                                          game_obj['rect'][2], game_obj['rect'][3],
                                                          color=game_obj['color'], obj_id=game_obj['id'])

          self.game_objects[game_obj['id']].render = False

    print(self.game_objects)
    return data

  def update(self, data):
    """override this method, only hook needed for the server"""
    if data['state'] == 'play':
      return self.play_state(data)
    else:
      ipdb.set_trace()

  def clear(self, data):
    """override this method, only hook needed for the server"""
    self.window.fill((0, 0, 0))

  def play_state(self, data):
    # TODO: why am I passing data in here?
    self.clear('Why does this need an argument?')
    for packet in data['game_objects']:
      translated_pos = self.translate_to_local(packet['location'])
      if translated_pos != 0:
        # TODO: don't translate here, do it in a better place
        packet['location'] = translated_pos
        self.game_objects[packet['id']].read_packet(packet)
      else:
        self.game_objects[packet['id']].render = False

    # TODO: this is what loop over game dict is for
    for obj_id, game_obj in self.game_objects.items():
      if game_obj.render:
        game_obj.draw(self.window)
    # obj_to_draw = [obj for obj in game_objects.items() if obj.render]
    # self.engine.map_attribute_flat(game_objects, 'draw')
    pygame.display.flip()

    data_struct = {'state': 'play'}
    return data_struct

  # TODO: actually do that.
  def translate_to_local(self, pos):
    """translates the given data to the local node. Wrapper for call to game
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
import libtcodpy as libtcod

#Screen size
SCREEN_WIDTH = 90
SCREEN_HEIGHT = 50

#Map size
MAP_WIDTH = 80
MAP_HEIGHT = 45

#FPS Limit (obviously)
LIMIT_FPS = 20

color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)

class Tile: 
	#A map tile and properties
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked
		
		#By default, if a tile is blocked, it also blocks sight
		if block_sight is None: 
			block_sight = blocked
		self.block_sight = block_sight


##################
## OBJECT CLASS ##
##################

class Object:
	#A generic object
	#Always represented by a char onscreen
	def __init__(self, x, y, char, color):
		self.x = x
		self.y = y
		self.char = char
		self.color = color
	
	def move(self, dx, dy):
		#If not blocked, move by a given amount
		if not map[self.x + dx][self.y + dy].blocked:
			self.x += dx
			self.y += dy
	
	def draw(self):
		#set the color and then draw the object
		libtcod.console_set_foreground_color(con, self.color)
		libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
		
	def clear(self):
		#erase the character that represents the object
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
	

####################
## Making the map ##
####################
	
def make_map():
	global map
	
	#Fill the map with unblocked, vision-penetrable tiles
	map = [[Tile(False)
		for y in range (MAP_HEIGHT) ]
			for x in range (MAP_WIDTH) ]
			
	map[30][22].blocked = True
	map[30][22].block_sight = True
	map[50][22].blocked = True
	map[50][22].block_sight = True
		
######################
## KEY HANDLING LOL ##
######################

def handle_keys():
	global playerx, playery
	
	key = libtcod.console_wait_for_keypress(True)
	#key = libtcod.console_check_for_keypress()
	
	#alt-enter fullscreens
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	#escape exits game
	elif key.vk == libtcod.KEY_ESCAPE:
		return True
	
	#movement key handling
	if libtcod.console_is_key_pressed(libtcod.KEY_UP):
		player.move(0, -1)
		
	elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
		player.move(0, 1)
	
	elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
		player.move(-1, 0)
	
	elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
		player.move(1, 0)
		
def render_all():
	global color_dark_wall
	global color_dark_ground
	
	#Go through tiles, set BG color
	for y in range (MAP_HEIGHT):
		for x in range (MAP_WIDTH):
			wall = map[x][y].block_sight
			if wall:
				libtcod.console_set_back(con, x, y, color_dark_wall, libtcod.BKGND_SET)
			else:
				libtcod.console_set_back(con, x, y, color_dark_ground, libtcod.BKGND_SET)
	
	#Draw all objects in the object list
	for object in objects:
		object.draw()
	
	#Blit the contents of the "con" console to the root console
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
		
def clear_all():
	#Clears all objects in the object list
	for object in objects:
		object.clear()

######################################
## INITIALIZATION AND MAIN LOOP LOL ##
######################################

libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'wait a tic')
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)


#Creating the player
player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.white)

#Creating an NPC
npc_0 = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2 + 2, '@', libtcod.yellow)

#Adding both to the list
objects = [npc_0, player]

#Generate the map
make_map()

while not libtcod.console_is_window_closed():
	libtcod.console_set_foreground_color(con, libtcod.white)
	
	render_all()
	
	libtcod.console_flush()
	
	clear_all()
		
	exit = handle_keys()
	if exit:
		break

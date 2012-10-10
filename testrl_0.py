import libtcodpy as libtcod
import math
import textwrap
import testrl_stuff
import shelve

#Screen size
SCREEN_WIDTH = 90
SCREEN_HEIGHT = 60

#Map size
MAP_WIDTH = 80
MAP_HEIGHT = 43

#Dungeon parameters
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

#Population parameters


#Base stat parameters
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

#Item parameters


#FPS Limit (obviously)
LIMIT_FPS = 12

#FoV settings
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

#GUI parameters
BAR_WIDTH = 20
PANEL_HEIGHT = 17
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50

LEVEL_SCREEN_WIDTH = 40

CHARACTER_SCREEN_WIDTH = 30

#Spell values
HEAL_AMOUNT = 4

LIGHTNING_RANGE = 5
LIGHTNING_DAMAGE = 20

CONFUSE_NUM_TURNS = 8
CONFUSE_RANGE = 8

FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12

####################
## Color settings ##
####################

#Wall
color_light_wall = libtcod.darker_grey
color_dark_wall = libtcod.Color(10, 10, 10)

#Ground
color_light_ground = libtcod.dark_grey
color_dark_ground = libtcod.Color(15, 15, 15)


#####################
## Rectangle Class ##
#####################

class Rect:
	#A rectangle class that is... well, surprise, a map rectangle
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h
		
        def center(self):
                center_x = (self.x1 + self.x2) / 2
                center_y = (self.y1 + self.y2) / 2
                return (center_x, center_y)

        def intersect(self, other):
                #Returns true if the rectangle intersects with ahother one
                return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                        self.y1 <= other.y2 and self.y2 >= other.y1)


################
## Tile Class ##
################

class Tile: 
	#A map tile and properties
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked
		self.explored = False
		
		#By default, if a tile is blocked, it also blocks sight
		if block_sight is None: 
			block_sight = blocked
		self.block_sight = block_sight


##################
## Object class ##
##################

class Object:
	#A generic object
	#Always represented by a char onscreen
	def __init__(self, x, y, char, name, color, blocks = False, combat = None, ai = None, item = None, always_visible = False):
                self.name = name
                self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.combat = combat
		self.always_visible = always_visible
		if self.combat: #let the combat component know who owns it
                        self.combat.owner = self

                self.ai = ai
                if self.ai: #let the ai component know who owns it
                        self.ai.owner = self

                self.item = item
                if self.item: #let the Item component know who owns it
                        self.item.owner = self
	
	def move(self, dx, dy):
		#If not blocked, move by a given amount
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy

	def move_towards(self, target_x, target_y):
                #vector from this object to the target, and distance
                dx = target_x - self.x
                dy = target_y - self.y
                distance = math.sqrt(dx **2 + dy **2)

                #normalize length to 1, preserving direction, then round it and convert to int so movement is by map grid
                dx = int(round(dx/distance))
                dy = int(round(dy/distance))
                self.move(dx, dy)

        def distance_to(self, other):
                #returns distance to another object
                dx = other.x - self.x
                dy = other.y - self.y
                return math.sqrt(dx ** 2 + dy ** 2)

        def distance_to_coords(self, x, y):
                #Returns the distance to coordinates
                return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
	
	def draw(self):
		#set the color and then draw the object
                if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or (self.always_visible and map[self.x][self.y].explored)):
                        libtcod.console_set_foreground_color(con, self.color)
                        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
		
	def clear(self):
		#erase the character that represents the object
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

	def send_to_back(self):
                #make this object drawn first so everything else gets drawn above it
                global objects
                objects.remove(self)
                objects.insert(0, self)
	

###################
## Combat class ##
###################

class Combat:
        def __init__(self, hp, defense, power, xp, death_function = None):
                self.max_hp = hp
                self.hp = hp
                self.defense = defense
                self.power = power
                self.xp = xp
                self.death_function = death_function

        def take_damage(self, damage):
                #apply damage if possible
                if damage > 0:
                        self.hp -= damage
                        #check for death
                        if self.hp <= 0:
                                function = self.death_function
                                if function is not None:
                                        function(self.owner)
                                        if self.owner != player:
                                                player.combat.xp += self.xp
                                        
        def attack(self, target):
                damage = self.power - target.combat.defense

                if damage > 0:
                        #make the target take damage
                        message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' damage.')
                        target.combat.take_damage(damage)
                else:
                        message(self.owner.name.capitalize() + ' attacks ' + target.name + ', but it has no effect!')

        def heal(self, amount):
                #heal by a given amount
                self.hp += amount
                if self.hp > self.max_hp:
                        self.hp = self.max_hp


############################
## Basic Monster AI stuff ##
############################

class BasicMonster:
        #AI for a basic monster
        def take_turn(self):
                #print 'The ' + self.owner.name + ' growls!'
                monster = self.owner
                if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
                        #move towards the player if too far
                        if monster.distance_to(player) >= 2:
                                monster.move_towards(player.x, player.y)

                        #if close enough to attack, do so
                        elif player.combat.hp > 0:
                                monster.combat.attack(player)
class ConfusedMonster:
        #AI for temporarily confused monsters
        def __init__(self, old_ai, num_turns = CONFUSE_NUM_TURNS):
                self.old_ai = old_ai
                self.num_turns = num_turns

        def take_turn(self):
                if self.num_turns > 0: #still confused...
                        #move in a random direction, decrease turns left confused
                        self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
                        self.num_turns -= 1

                else:
                        self.owner.ai = self.old_ai
                        message('The ' + self.owner.name + ' is no longer confused.', libtcod.red)


################
## Item class ##
################

class Item:
        #an item that can be picked up and used, such as a potion or a sword
        def __init__(self, use_function = None):
                self.use_function = use_function
        
        def pick_up(self):
                #add to the acquirer's inventory and remove from the map
                if len(inventory) >= 26:
                        message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
                else:
                        inventory.append(self.owner)
                        objects.remove(self.owner)
                        message('You picked up a ' + self.owner.name + ' and shove it in your backpack.', libtcod.green)

        def use(self):
                #just call the use_function if it is defined
                if self.use_function is None:
                        message('The ' + self.owner.name + ' cannot be used')
                else:
                        if self.use_function() != 'cancelled':
                                inventory.remove(self.owner)#destroy after use

        def drop(self):
                #add to the map, remove from player inventory, at player coords
                objects.append(self.owner)
                inventory.remove(self.owner)
                self.owner.x = player.x
                self.owner.y = player.y
                message ('You drop the ' + self.owner.name + '.', libtcod.yellow)

                
####################
## Making the map ##
####################
	
def make_map():
	global map, objects, stairs

	#List of objects with just the player
	objects = [player]
	
	#Fill the map with blocked tiles
	map = [[Tile(True)
		for y in range (MAP_HEIGHT) ]
			for x in range (MAP_WIDTH) ]

        rooms = []
        num_rooms = 0
        for r in range(MAX_ROOMS):
                #random witdth and height
                w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
                h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		#random position without going outside the boundaries of the map
                x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
                y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

                #rect class makes rectangles easier to work with
                new_room = Rect(x, y, w, h)

                #run through new rooms to see if they intersect with this one
                failed = False
                for other_room in rooms:
                        if new_room.intersect(other_room):
                                failed = True
                                break

                if not failed:
                        #this means no intersections, so it's valid
                        create_room(new_room)

                        #Puts things in the room
                        place_objects(new_room)

                        #Center coordinates of the room, will be useful
                        (new_x, new_y) = new_room.center()

                        if num_rooms == 0:
                                #This is the first room, player starts here
                                player.x = new_x
                                player.y = new_y

                        else:
                                #All rooms after the first one
                                #Connect to previous room with a tunnel

                                #Center coords of previous room
                                (prev_x, prev_y) = rooms[num_rooms - 1].center()

                                #Draw a coin (random number either 0 or 1)
                                if libtcod.random_get_int(0, 0, 1) == 1:
                                        #First move is horizontal, then vertical
                                        create_h_tunnel(prev_x, new_x, prev_y)
                                        create_v_tunnel(prev_y, new_y, new_x)
                                else:
                                        #First move is vertical, then horizontal
                                        create_v_tunnel(prev_y, new_y, new_x)
                                        create_h_tunnel(prev_x, new_x, prev_y)
                        #Append the room to the list
                        rooms.append(new_room)
                        num_rooms += 1
                        
        #Finally, create stairs down to the next level
        stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, always_visible = True)
        objects.append(stairs)
                        

def create_room(room):
	global map
	for x in range (room.x1 + 1, room.x2):
		for y in range (room.y1 + 1, room.y2):
			map[x][y].blocked = False
			map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
	global map
	#horizontal tunnel. min() and max() are used in case x1>x2
	for x in range(min(x1, x2), max(x1, x2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
	global map
	#Vertical tunnel, min and max are used in case y1>y2
	for y in range(min(y1, y2), max(y1, y2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False


#########################
## Next level function ##
#########################
		
def next_level():
        global dungeon_level
        
        #Advance to the next level
        message('You take a moment to rest and recover your strength', libtcod.light_violet)
        player.combat.heal(player.combat.max_hp / 2) #Heal half of the player's HP

        message('After a rare moment of peace, you descend deeper...', libtcod.red)
        dungeon_level += 1
        make_map() #Create a fresh level
        initialize_fov()


########################
## Populating the map ##
########################

def place_objects(room):
        place_monsters(room)
        place_items(room)

## Monster placement ##

def place_monsters(room):
        #Monster time
        #Max number of monsters per room
        max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]])

        #Chance each monster has of spawning
        monster_chances = {}
        monster_chances['orc'] = 70
        monster_chances['troll'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])
        monster_chances['goblin'] = from_dungeon_level([[25, 1], [20, 3], [15, 5], [10, 7]])
        monster_chances['wat'] = 10

        #Choose random number of monsters for this room
        num_monsters = libtcod.random_get_int(0, 0, max_monsters)
        
        for i in range(num_monsters):
                #choose random spot for this monster
                x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
                y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
                
                #As long as the place isn't blocked, it'll make a monster 
                if not is_blocked(x, y):
                        #Roll to see what it is
                        choice = random_choice(monster_chances)

                        #Various resulting cases
                        if choice == 'orc':
                                #Create an orc
                                combat_component = Combat(hp = 10, defense = 0, power = 3, xp = 35, death_function = monster_death)
                                ai_component = BasicMonster()
                                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks = True, combat = combat_component, ai = ai_component)
                                
                        elif choice == 'troll':
                                #Create a troll
                                combat_component = Combat(hp = 16, defense = 1, power = 4, xp = 100, death_function = monster_death)
                                ai_component = BasicMonster()
                                monster = Object(x, y, 'T', 'troll', libtcod.orange, blocks = True, combat = combat_component, ai = ai_component)
                                
                        elif choice == 'goblin':
                                #Create a goblin
                                combat_component = Combat(hp = 7, defense = 0, power = 3, xp = 20, death_function = monster_death)
                                ai_component = BasicMonster()
                                monster = Object(x, y, 'g', 'goblin', libtcod.grey, blocks = True, combat = combat_component, ai = ai_component)
                                
                        elif choice == 'wat':
                                #Create a wat
                                combat_component = Combat(hp = 2, defense = 4, power = 1, xp = 5, death_function = monster_death)
                                ai_component = BasicMonster()
                                monster = Object(x, y, 'W', 'wat', libtcod.pink, blocks = True, combat = combat_component, ai = ai_component)

                        #Append it to the objects list
                        objects.append(monster)

## Item placement ##
                        
def place_items(room):
        #Item time
        #Max number of items per room
        max_items = from_dungeon_level([[1, 1], [2, 4]])

        #List of item chances
        item_chances = {}
        item_chances['potion_healing'] = 60
        item_chances['scroll_lightning'] = 10
        item_chances['scroll_fireball'] = 10
        item_chances['scroll_confusion'] = 10

        #Choose a random number of items for this room
        num_items = libtcod.random_get_int(0, 0, max_items)

        for i in range(num_items):
                #choose random spot for the item
                x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
                y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

                #only place if tile is not blocked
                if not is_blocked(x, y):
                        #choose a random item
                        choice = random_choice(item_chances)
                        if choice == 'potion_healing':
                                #Create a healing potion
                                item_component = Item(use_function = cast_heal)
                                item = Object(x, y, '!', 'healing potion', libtcod.violet, item = item_component)

                        elif choice == 'scroll_lightning':
                                #Create a lightning bolt scroll
                                item_component = Item(use_function = cast_lightning)
                                item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item = item_component)

                        elif choice == 'scroll_confusion':
                                #Create a confusion scroll
                                item_component = Item(use_function = cast_confuse)
                                item = Object(x, y, '#', 'scroll of confusion', libtcod.light_yellow, item = item_component)

                        elif choice == 'scroll_fireball':
                                #Create a fireball scroll
                                item_component = Item(use_function = cast_fireball)
                                item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, item = item_component)
                        
                        #append it to the list
                        objects.append(item)
                        #draw it behind everything
                        item.send_to_back()


## Index for random selection

def random_choice_index(chances): #Chose one option from a list of chances, returns the index
        #The dice will land on some number between 1 and the sum of the chances
        dice = libtcod.random_get_int(0, 1, sum(chances))

        #Go through the chances, keeping the sum so far
        running_sum = 0
        choice = 0
        for w in chances:
                running_sum += w

                #See if the dice landed in the part that corresponds to this choice
                if dice <= running_sum:
                        return choice
                choice += 1

## String random choice, easier to read ##
                
def random_choice(chances_dict):
        #Choose one option from a dictionary of chances, returns its key
        chances = chances_dict.values()
        strings = chances_dict.keys()

        return strings[random_choice_index(chances)]

## Dungeon level progression table ##

def from_dungeon_level(table):
        #Returns a value that depends on evel. Table specifies what will occur on each leve, default is 0
        for (value, level) in reversed(table):
                if dungeon_level >= level:
                        return value
        return 0


##################
## Key handling ##
##################

def handle_keys():
	global playerx, playery
	global fov_recompute
	
	#key = libtcod.console_wait_for_keypress(True)
	key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)
	
	#alt-enter fullscreens
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
		
	#escape exits game
	elif key.vk == libtcod.KEY_ESCAPE:
		return 'exit'

	if game_state == 'playing':
                #movement key handling
                if libtcod.console_is_key_pressed(libtcod.KEY_KP1):
                        player_move_or_attack(-1, 1)

                elif libtcod.console_is_key_pressed(libtcod.KEY_KP2):
                        player_move_or_attack(0, 1)
                        
                elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
                        player_move_or_attack(1, 1)
                
                elif libtcod.console_is_key_pressed(libtcod.KEY_KP4):
                        player_move_or_attack(-1, 0)

                elif libtcod.console_is_key_pressed(libtcod.KEY_KP5):
                        player_move_or_attack(0, 0)
                
                elif libtcod.console_is_key_pressed(libtcod.KEY_KP6):
                        player_move_or_attack(1, 0)

                elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
                        player_move_or_attack(-1, -1)

                elif libtcod.console_is_key_pressed(libtcod.KEY_KP8):
                        player_move_or_attack(0, -1)

                elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
                        player_move_or_attack(1, -1)
                

		else:
                        #test for other keys
                        key_char = chr(key.c)

                        if key_char == 'g':
                                #pick up an item
                                for object in objects: #look for an item in the player's tile
                                        if object.x == player.x and object.y == player.y and object.item:
                                                object.item.pick_up()
                                                break

                        if key_char == 'i':
                                #show the inventory, if item is selected, use it
                                chosen_item = inventory_menu('Press the key next to an item to use it, or any other key to cancel.\n')
                                if chosen_item is not None:
                                        chosen_item.use()

                        if key_char == 'd':
                                #Show the inventory, if item is selected, drop it
                                chosen_item = inventory_menu('Press the key next to an item to drop it, or any other key to cancel\n')
                                if chosen_item is not None:
                                        chosen_item.drop()

                        if key_char == '<':
                                #Go down the stairs, if player is on them
                                if stairs.x == player.x and stairs.y == player.y:
                                        next_level()

                        if key_char == 'c':
                                #Open the character screen
                                character_menu()
                                

                        return 'didnt-take-turn'

                
##################################
## Movement and attack handling ##
##################################

def player_move_or_attack(dx, dy):
        global fov_recompute

        #coords that the player's moving to
        x = player.x + dx
        y = player.y + dy

        #try to attack first
        target = None
        for object in objects:
                if object.combat and object.x == x and object.y == y:
                        target = object
                        break

        #attack if target found, move elsewise
        if target is not None and target is not player:
                player.combat.attack(target)
        else:
                player.move(dx, dy)
                fov_recompute = True


######################################
## Rendering and clearing functions ##
######################################

def render_all():
	global color_dark_wall, color_light_wall
	global color_dark_ground, color_light_ground
	global fov_recompute

	if fov_recompute:
                #recompute FOV if needed (such as player movement or spellcasting or light or something)
                fov_recompute = True
                libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
	
                #Go through tiles, set BG color
                for y in range (MAP_HEIGHT):
                        for x in range (MAP_WIDTH):
                                visible = libtcod.map_is_in_fov(fov_map, x, y)
                                wall = map[x][y].block_sight
                                if not visible:
                                        #Even if it isn't visible it should be "remembered"
                                        if map[x][y].explored:
                                                #out of player FOV
                                                if wall:
                                                        libtcod.console_set_back(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                                                else:
                                                        libtcod.console_set_back(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                                else:
                                        #it is visible
                                        if wall:
                                                libtcod.console_set_back(con, x, y, color_light_wall, libtcod.BKGND_SET)
                                        else:
                                                libtcod.console_set_back(con, x, y, color_light_ground, libtcod.BKGND_SET)
                                        map[x][y].explored = True
                                        
                #Draw all objects in the object list
                for object in objects:
                        if object != player:
                                object.draw()
                player.draw()
                
                #Blit the contents of the "con" console to the root console
                libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

                #prepare to render GUI panels
                libtcod.console_set_background_color(panel, libtcod.black)
                libtcod.console_clear(panel)

                #print the game messages one line at a time
                y = 1
                for (line, color) in game_msgs:
                        libtcod.console_set_foreground_color(panel, color)
                        libtcod.console_print_left(panel, MSG_X, y, libtcod.BKGND_NONE, line)
                        y += 1

                #show player's stats
                render_bar(1, 1, BAR_WIDTH, 'HP', player.combat.hp, player.combat.max_hp, libtcod.light_red, libtcod.darker_red)
                libtcod.console_print_left(panel, 1, 3, libtcod.BKGND_NONE, 'Dungeon level ' + str(dungeon_level))

                #Display names of things under mouse
                libtcod.console_set_foreground_color(panel, libtcod.light_gray)
                libtcod.console_print_left(panel, 1, 0, libtcod.BKGND_NONE, get_names_under_mouse())
                
                #blit the contents of the 'panel' to the root console
                libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
		
def clear_all():
	#Clears all objects in the object list
	for object in objects:
		object.clear()


######################
## Blocking section ##
######################

def is_blocked(x, y):
        #first test the map tile
        if map[x][y].blocked:
                return True

        #now check for any blocking objects
        for object in objects:
                if object.blocks and object.x == x and object.y == y:
                        return True

        return False

#####################
## Death Functions ##
#####################

def player_death(player):
        #the game over'd
        global game_state
        message('You died!')
        game_state = 'dead'

        #for added effect, make player corpse
        player.char = '%'
        player.color = libtcod.dark_red

def monster_death(monster):
        #make it into a corpse, can be moved through, doesn't move
        message(monster.name.capitalize() + ' has died. You gain ' + str(monster.combat.xp) + ' experience points', libtcod.orange)
        monster.char = '%'
        monster.color = libtcod.dark_red
        monster.combat = False
        monster.blocks = False
        monster.ai = None
        monster.name = 'remains of ' + monster.name
        monster.send_to_back()
        monster.draw()

###################
## Spell effects ##
###################
        
def cast_heal():
        #heal the player
        if player.combat.hp == player.combat.max_hp:
                message('You are already at full health.', libtcod.red)
                return 'cancelled'

        message ('Your wounds stretch together and seal. Gross.', libtcod.light_violet)
        player.combat.heal(HEAL_AMOUNT)

def cast_lightning():
        #finds closest enemy inside a max range and lightnings the fuck out of it
        monster = closest_monster(LIGHTNING_RANGE)
        if monster is None: #no enemy within max range
                message ('No enemy is close enough to strike.', libtcod.red)
                return 'cancelled'

        #the lightning part
        message ('Lightning strikes the ' + monster.name + ', doing ' + str(LIGHTNING_DAMAGE) + ' damage.', libtcod.light_blue)
        monster.combat.take_damage(LIGHTNING_DAMAGE)

def cast_confuse():
        #finds closest in-range enemy and confuses it
        message ('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
        monster = target_monster(CONFUSE_RANGE)
        if monster is None:
                return 'cancelled'

        #Replace monster's AI with the confused one, after it turns off it will gain normal AI again
        old_ai = monster.ai
        monster.ai = ConfusedMonster(old_ai)
        monster.ai.owner = monster #tell the new component who owns it
        message ('The eyes of the ' + monster.name + ' look vacant, as it starts to stumble around...', libtcod.light_green)

def cast_fireball():
        #asks the player for a target tile to throw a fireball at
        message ('Left-click a target tile for the fireball, right-click to cancel', libtcod.light_cyan)
        (x, y) = target_tile()
        if x is None:
                return 'cancelled'
        message ('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles.', libtcod.orange)

        #Does the damage
        for obj in objects:
                if obj.distance_to_coords(x, y) <= FIREBALL_RADIUS and obj.combat:
                        message ('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' damage.', libtcod.orange)
                        obj.combat.take_damage(FIREBALL_DAMAGE)


#########################################
## Leveling up and player modification ##
#########################################

def check_level_up():
        #see if the player's experience is enough to level-up
        level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
        if player.combat.xp >= level_up_xp:
                #it is! level up and ask to raise some stats
                player.level += 1
                player.combat.xp -= level_up_xp
                
                message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)

                choice = None
                while choice == None:  #keep asking until a choice is made
                        choice = menu('Level up! Choose a stat to raise:\n',
                        ['Constitution (+20 HP, from ' + str(player.combat.max_hp) + ')',
                        'Strength (+1 attack, from ' + str(player.combat.power) + ')',
                        'Agility (+1 defense, from ' + str(player.combat.defense) + ')'], LEVEL_SCREEN_WIDTH)

                if choice == 0:
                        player.combat.max_hp += 20
                        player.combat.hp += 20

                elif choice == 1:
                        player.combat.power += 1

                elif choice == 2:
                        player.combat.defense += 1

#######################
## Targeting section ##
#######################
        
def closest_monster(max_range):
        #find closest enemy, up to a maximum range, and in the player's FoV
        closest_enemy = None
        closest_dist = max_range + 1 #start with slightly over max range

        for object in objects:
                if object.combat and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
                        #calculate distance between object and player
                        dist = player.distance_to(object)
                        if dist < closest_dist: #If it is closer than the previous
                                closest_enemy = object
                                closest_dist = dist
                                
        return closest_enemy

def target_tile(max_range = None):
        #return the position of a left-cliked in player's FoV, and optionally in a range, or (none, none) if right-clicked
        while True:
                render_all()
                libtcod.console_flush()

                key = libtcod.console_check_for_keypress()
                mouse = libtcod.mouse_get_status()
                (x, y) = (mouse.cx, mouse.cy)

                #Returns the mouse position 
                if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
                    max_range is None or player.distance_to_coords(x, y) <= max_range):
                        return (x, y)

                #Cancel if the player presses the right mouse or escape
                if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
                        return (None, None)

def target_monster(max_range = None):
        #returns a clicked monster inside FoV up to a range, or None if right-clicked
        while True:
                (x, y) = target_tile(max_range)
                if x is None: #player cancelled
                        return None

                #return the first clicked monster, otherwise continue looping
                for obj in objects:
                        if obj.x == x and obj.y == y and obj.combat:
                                return obj
        

###############
## GUI Stuff ##
###############

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
        #render a bar for tracking something. First comes width.
        bar_width = int(float(value) / maximum * total_width)

        #render the background first
        libtcod.console_set_background_color(panel, back_color)
        libtcod.console_rect(panel, x, y, total_width, 1, False)

        #Now render the bar on top
        libtcod.console_set_background_color(panel, bar_color)
        if bar_width > 0:
                libtcod.console_rect(panel, x, y, bar_width, 1, False)

        #And some centered text with values for clarity
        libtcod.console_set_foreground_color(panel, libtcod.white)
        libtcod.console_print_center(panel, x + total_width / 2, y, libtcod.BKGND_NONE, name + ': ' + str(value) + '/' + str(maximum))

def clear_messages():
        global game_msgs
        game_msgs = []

def message(new_msg, color = libtcod.white):
        #split the message if necessary and word wrap
        new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

        for line in new_msg_lines:
                #if the buffer is full, remove the first line to make room for the new one
                if len(game_msgs) == MSG_HEIGHT:
                        del game_msgs[0]

                #add the new line as a tuple, with the text and color
                game_msgs.append((line, color))

def get_names_under_mouse():
        #return a string with the names of all objects under the mouse
        mouse = libtcod.mouse_get_status()
        (x, y) = (mouse.cx, mouse.cy)

        #create a list with names of all objects at the mouse's coords and in FoV
        names = [obj.name for obj in objects
                 if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

        names = ', '.join(names)
        return names.capitalize()

## Inventory and menus ##

def menu(header, options, width):
        
        if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options')
        #calculate height for the header after auto-wrap and one line per option
        header_height = libtcod.console_height_left_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
        if header == '':
                header_height = 0
        height = len(options) + header_height

        #Create an off-screen console that represents the menu window
        window = libtcod.console_new(width, height)

        #Print the header with auto-wrap
        libtcod.console_set_foreground_color(window, libtcod.white)
        libtcod.console_print_left_rect(window, 0, 0, width, height, libtcod.BKGND_NONE, header)

        #Print all the options
        y = header_height
        letter_index = ord('a')
        for option_text in options:
                text = '(' + chr(letter_index) + ')' + option_text
                libtcod.console_print_left(window, 0, y, libtcod.BKGND_NONE, text)
                y += 1
                letter_index += 1

        #Blit the contents of "window" to the root console
        x = SCREEN_WIDTH/2 - width/2
        y = SCREEN_HEIGHT/2 - height/2
        libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

        #Present the player with the root console and wait for a key-press
        libtcod.console_flush()
        key = libtcod.console_wait_for_keypress(True)

        #Convert the ASCII code to an index, and if it corresponds an option, return it
        index = key.c - ord('a')
        if index >= 0 and index < len(options):
                return index

        #alt-enter fullscreens
        if key.vk == libtcod.KEY_ENTER and key.lalt:
                libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        return None

def msgbox(text, width = 50):
        menu(text, [], width) #use menu as a sort of message delivery box thing

def inventory_menu(header):
        #Show a menu with each item of the inventory as an option
        if len(inventory) == 0:
                options = ['Inventory is empty']
        else:
                options = [item.name for item in inventory]

        index = menu(header, options, INVENTORY_WIDTH)
        if index is None or len(inventory) == 0:
                return None
        return inventory[index].item

def character_menu():
        #Open the character stat screen
        level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
        msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.combat.xp) +
                '\nNext level: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.combat.max_hp) +
                '\nAttack: ' + str(player.combat.power) + '\nDefense: ' + str(player.combat.defense), CHARACTER_SCREEN_WIDTH)

##################################
## Saving and loading functions ##
##################################

def save_game():
        #open a new empty shelve (possibly overwriting an old one) to write the game data
        file = shelve.open('savegame', 'n')
        file['map'] = map
        file['objects'] = objects
        file['player_index'] = objects.index(player) #player objects in the list
        file['inventory'] = inventory
        file['game_msgs'] = game_msgs
        file['game_state'] = game_state
        file['stairs_index'] = objects.index(stairs)
        file['dungeon_level'] = dungeon_level
        file.close()

def load_game():
        #Open a previously saved shelve and load the game data
        global map, objects, player, inventory, game_msgs, game_state, dungeon_level, stairs

        file = shelve.open('savegame', 'r')
        map = file['map']
        objects = file['objects']
        player = objects[file['player_index']] #Get index of player in objects list, access it
        stairs = objects[file['stairs_index']]
        inventory = file['inventory']
        game_msgs = file['game_msgs']
        game_state = file['game_state']
        dungeon_level = file['dungeon_level']
        file.close()

        initialize_fov()



######################################
## INITIALIZATION AND MAIN LOOP LOL ##
######################################

## Declaring and instantiating stuff ##

libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_set_custom_font('lucida12x12_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'wait a tic')
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

## GUI Shenanigans ##

#HP Bar
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

## Start the new game ## 
def new_game():
        global player, inventory, game_msgs, game_state, dungeon_level

        #create object representing the player
        combat_component = Combat(hp = 30, defense = 2, power = 5, xp = 0, death_function = player_death)
        player = Object(0, 0, '@', 'Player', libtcod.white, blocks = True, combat = combat_component)
        player.level = 1

        #Generate the map, but not yet drawn to the screen
        dungeon_level = 1
        make_map()

        #Initialize the FoV
        initialize_fov()
        
        #Set the game state
        game_state = 'playing'
        inventory = []

        #creates the list of messages and colors
        game_msgs = []

        #Welcome message
        message('Why you are here is not the question, but rather how long you plan to survive. Good luck.', libtcod.red)

## Moderate FoV ##
def initialize_fov():
        global fov_recompute, fov_map
        fov_recompute = True

        #Create the FoV map, according to generated map
        fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
        for y in range (MAP_HEIGHT):
                for x in range (MAP_WIDTH):
                        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

        libtcod.console_clear(con) #unexplored areas start as default background color


## Menu functions ##
def main_menu():
        img = libtcod.image_load('menu_background1.png')
        
        while not libtcod.console_is_window_closed():
                #show the background image, at twice the regular console resolution
                libtcod.image_blit_2x(img, 0, 0, 0)

                #Show game details, credits, etc
                libtcod.console_set_foreground_color(0, libtcod.light_yellow)
                libtcod.console_print_center(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, 'The Frontier')
                libtcod.console_print_center(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, 'By Winkle and Littlefoot')

                #show options and wait for the player's choice
                choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)
                
                if choice == 0: #New game
                        new_game()
                        play_game()

                if choice == 1: #Load last save game
                        try:
                                load_game()
                        except:
                                msgbox('\n No save game to load\n', 24)
                                continue
                        play_game()
                        
                elif choice == 2: #Quit
                        break

## The actual main loop ##
def play_game():
        
        player_action = None
        while not libtcod.console_is_window_closed():

                #Render the screen
                render_all()

                #Flush console, check for level-up
                libtcod.console_flush()
                check_level_up()

                #Erase all objects at old locations before they move                
                clear_all()

                #Handle the keys, exit game or other special cases if necessary
                player_action = handle_keys()

                if player_action == 'exit':
                        save_game()
                        clear_messages()
                        break

                if game_state == 'playing' and player_action != 'didnt-take-turn':
                        for object in objects:
                                if object.ai:
                                        object.ai.take_turn()


main_menu()

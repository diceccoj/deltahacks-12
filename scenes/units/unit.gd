extends CharacterBody2D
class_name Unit

enum Type {
	UNKNOWN,
	WARRIOR,
	ARCHER,
	LANCER,
	MONK,
	PAWN
}

enum Team {
	Red,
	Blue
}

@export var type : Type
@export var move_speed : float = 100.0
@export var attack : float = 10.0
@export var total_hp : float = 20.0


var team : Team
var current_hp : float

@onready var sprite := $AnimatedSprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D




func spawn_and_setup(team_ : Team, start_pos : Vector2) -> void:
	team = team_
	
	position = start_pos
	
	current_hp = total_hp
	
	# set up team-based factors
	if team == Team.Red:
		collision_layer = 1 << 1
		collision_mask = (1 << 0) | (1 << 2)
		velocity.x = move_speed 
	else:
		sprite.flip_h = true
		collision_layer = 1 << 2
		collision_mask = (1 << 0) | (1 << 1)
		velocity.x = -move_speed
	
	animation_handler("idle")


func _process(delta: float):
	
	# jnth note: what is this for?
	if (team == Team.Red and velocity.x <= move_speed):
		velocity.x += move_speed * delta
	elif (velocity.x >= -move_speed):
		velocity.x += -move_speed * delta
	
	
	move_and_slide()
	for index in get_slide_collision_count():
		var clsn = get_slide_collision(index)
		var collided_obj := clsn.get_collider()
		#print("Collided with: ", body.name)
		if (collided_obj is Unit):
			if (collided_obj.team != team): attack_unit(collided_obj)
		elif (collided_obj is Tower):
			if (collided_obj.team != team):  attack_tower(collided_obj)
	
	if (current_hp == 0):
		perish()

func attack_unit(unit : Unit):
	animation_handler("attack")
	await sprite.animation_finished
	
	# check if user still exists because another unit may have killed it
	if (unit): unit.take_dmg(attack)

func attack_tower(tower : Tower):
	animation_handler("attack")
	await sprite.animation_finished
	tower.take_damage(attack)

# subtract hp (possibly update an hp bar?)
func take_dmg(dmg : float):
	current_hp = max(0.0, current_hp - dmg)

# delete unit and possibly add any additional effects/functions
func perish():
	self.queue_free()

# kicks user back when hit
func push_back():
	velocity.x = -move_speed if team == Team.Red else move_speed

# handles animation based on team
func animation_handler(anim : String):
	sprite.play(anim + ("_red" if team == Team.Red else "_blue"))

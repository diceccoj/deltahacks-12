extends CharacterBody2D
class_name Unit

enum Type {
	UNKNOWN,
	WARRIOR,
	ARCHER
}

@export var type : Type
@export var red_team : bool

@onready var sprite := $AnimatedSprite2D

var dir := 1


func _ready() -> void:
	velocity.x = 100
	if red_team:
		collision_layer = 1 << 1
		collision_mask = (1 << 0) | (1 << 2)  
	else:
		sprite.flip_h = true
		collision_layer = 1 << 2
		collision_mask = (1 << 0) | (1 << 1)
	
func _process(delta: float):
	
	if velocity.x <= dir * 100:
		velocity.x += dir * 100 * delta
		
	
	move_and_slide()

func push_back():
	velocity.x = -100 * dir

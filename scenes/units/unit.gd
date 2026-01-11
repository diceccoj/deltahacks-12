extends CharacterBody2D
class_name Unit

enum Type {
	UNKNOWN,
	WARRIOR,
	ARCHER
}

@export var type : Type

@onready var sprite := $AnimatedSprite2D

var flipped := false


func _ready() -> void:
	velocity.x = 100
	
func _process(delta: float):
	move_and_slide()

func push_back():
	pass

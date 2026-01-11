extends Unit
class_name Archer

const firing_delay : float = 4.0
var timer: Timer

const arrow_scene = preload("res://scenes/units/arrow.tscn")

@onready var arrow_bucket: Node = $ArrowBucket


func _ready() -> void:
	timer = Timer.new()
	add_child(timer)
	timer.wait_time = firing_delay
	timer.timeout.connect(fire_arrow)
	timer.start()
	animation_handler("run")

func _process(delta: float):
	# jnth note: what is this for?
	if (team == Team.Red and velocity.x <= move_speed):
		velocity.x += move_speed * delta
	elif (velocity.x >= -move_speed):
		velocity.x += -move_speed * delta
	
	move_and_slide()
	
	if (current_hp <= 0):
		perish()

# play animation, fire arrow, and start timer
func fire_arrow():
	velocity.x = 0.0
	animation_handler("attack")
	var arrow : Arrow = arrow_scene.instantiate()
	arrow.team = team
	arrow_bucket.add_child(arrow)
	arrow.position = self.position
	
	timer.start()

# archer should never attack head on
func attack_unit(_unit : Unit):
	pass
func attack_tower(_tower : Tower):
	pass

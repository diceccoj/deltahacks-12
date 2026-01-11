extends Unit

class_name Monk

@onready var blast_radius: Area2D = $BlastRadius

var within_blast : Array[Unit] = []


func _on_blast_radius_body_entered(body: Node2D) -> void:
	if (body is Unit):
		within_blast.append(body)


func _on_blast_radius_body_exited(body: Node2D) -> void:
	if (body is Unit):
		within_blast.remove_at(within_blast.find(body))

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
			if (collided_obj.team != team): kaboom()

	if (current_hp <= 0):
		perish()

# monk destroys everything in radius. Including allies
func kaboom():
	sprite.play("kaboom?")
	await sprite.animation_finished
	for unit in within_blast:
		unit.take_dmg(20)
	perish()

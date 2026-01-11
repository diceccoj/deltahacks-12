extends Sprite2D
class_name Arrow

var team : Unit.Team
const dmg : float = 5.0
var speed : float = 100.0

func _ready() -> void:
	# reverse velocity for blue team
	if (team == Unit.Team.Blue):
		flip_h = true
		speed = -speed

func _process(delta: float) -> void:
	position.x = position.x + delta * speed
	

func _on_area_2d_body_entered(body: Node2D) -> void:
	if (body is Unit or body is Monk):
		if (team != body.team):
			body.take_dmg(dmg)
			body.velocity.x = 0
			self.queue_free()

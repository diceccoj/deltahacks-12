extends Area2D
class_name Tower

signal died

enum Team {
	Red,
	Blue
}

@export var team : Team

var max_health := 50.0
var health : float
var bar_scale := 1.0

func _ready():
	health = max_health

func take_damage(damage: float):
	health -= damage
	if health < 0.0:
		died.emit()
	health = max(0.0, health)
	
	var t := create_tween()
	t.tween_property(self, ^"modulate", Color.RED, 0.1)
	t.chain().tween_property(self, ^"modulate", Color.WHITE, 0.1)
	var t2 := create_tween()
	t2.tween_property($HealthBar, ^"scale", Vector2(float(health) / max_health, 1), 0.6).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)


func _on_body_entered(body: Node2D) -> void:
	if body is Unit:
		body.push_back()
		take_damage(1)

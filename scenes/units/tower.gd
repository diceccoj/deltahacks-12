extends Area2D
class_name Tower

@onready var explosion_effect: AnimatedSprite2D = $ExplosionEffect


signal died
var tower_fallen = false

enum Team {
	Red,
	Blue
}

@export var team : Team

var max_health := 150.0
var health : float
var bar_scale := 1.0

func _ready():
	health = max_health
	explosion_effect.play("default")

func take_damage(damage: float):
	health -= damage
	if health <= 0.0:
		tower_fall()
	health = max(0.0, health)
	
	var t := create_tween()
	t.tween_property(self, ^"modulate", Color.RED, 0.1)
	t.chain().tween_property(self, ^"modulate", Color.WHITE, 0.1)
	var t2 := create_tween()
	t2.tween_property($HealthBar, ^"scale", Vector2(float(health) / max_health, 1), 0.6).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)


func _on_body_entered(body: Node2D) -> void:
	if body is Unit:
		if body.team != team:
			body.push_back()
			body.attack_tower(self)
	if body is Monk:
		if body.team != team:
			body.kaboom()

# queued when tower falls
func tower_fall():
	explosion_effect.play("tower_kaboom")
	await explosion_effect.animation_finished
	died.emit()

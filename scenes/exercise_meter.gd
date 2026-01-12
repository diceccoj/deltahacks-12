extends Control
class_name ExerciseMeter

@export var color : Color
@export var exercise : PoseServer.Exercise

var readied := false
var progress : float = 0.0

func set_progress(p: float):
	progress = p
	var t := create_tween()
	t.tween_property($Panel/Progress, ^"scale", Vector2(1, progress), 0.3).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)

func set_readied(b: bool):
	readied = b
	if readied:
		$Label.visible = true
	else:
		$Label.visible = false

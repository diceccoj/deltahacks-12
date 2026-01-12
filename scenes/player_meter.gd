extends Control
class_name PlayerMeter

var move_list : Dictionary[PoseServer.Exercise, ExerciseMeter] = {
	
}

# make a dictionary of exercises
func _ready() -> void:
	for child in get_children():
		if (child is ExerciseMeter):
			move_list[child.exercise] = child

extends Node2D


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	$Server1Debug.text = str($P1Pose.server.is_connection_available())


func _on_p_1_pose_pose_changed(pose: String) -> void:
	$Pose1Debug.text = "Player 1 did: " + pose

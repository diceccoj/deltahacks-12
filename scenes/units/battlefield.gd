extends Node2D


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	$Server1Debug.text = str($P1Pose.camera_data[0]["server"].is_connection_available())
	#
	#var pose1 : String = $P1Pose.cur_pose
	#$Pose1Debug.text = "Player 1 did: " + pose1
	#if Input.is_key_pressed(KEY_Q):
		#pose1 = "jumping "
	#elif Input.is_key_pressed(KEY_W):
		#
	#elif Input.is_key_pressed(KEY_E):
		#
	#elif Input.is_key_pressed(KEY_R):
		#
	#elif Input.is_key_pressed(KEY_T):
	
	


func _on_p_1_pose_pose_changed(camera_id: int, pose: String) -> void:
	$Pose1Debug.text = "Player 1 did: " + pose


func _on_p_1_pose_mask_updated(camera_id: int, texture: ImageTexture) -> void:
	var image = texture.get_image()
	var data = image.get_data()
	if camera_id == 0:
		$Mask1.texture = texture
	else:
		$Mask2.texture = texture

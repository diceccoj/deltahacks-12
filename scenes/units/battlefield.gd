extends Node2D
class_name Battlefield

@onready var py_bridge := $PyBridge

@onready var red_tower: Tower = $RedTower
@onready var blue_tower: Tower = $BlueTower
@onready var unit_bucket: Node = $UnitBucket

@onready var red_start_pos: Marker2D = $LMid
@onready var blue_start_pos: Marker2D = $RMid

@onready var pose_server: PoseServer = $Poses
@onready var endscreen: Endscreen = $Endscreen


enum Lane {Left, Right}

var units_lib: Dictionary[Unit.Type, PackedScene] = {
	Unit.Type.WARRIOR: preload("res://scenes/units/warrior.tscn"),
	Unit.Type.ARCHER: preload("res://scenes/units/archer.tscn"),
	Unit.Type.PAWN: preload("res://scenes/units/pawn.tscn"),
	Unit.Type.LANCER: preload("res://scenes/units/lancer.tscn"),
	Unit.Type.MONK: preload("res://scenes/units/monk.tscn")
}

var positions_lib: Dictionary[Unit.Team, Dictionary]


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	#$"../FadeAnimation/AnimationPlayer"
	
	positions_lib = {
		Unit.Team.Red: {
			Lane.Left: $LTop.position,
			Lane.Right: $LBot.position
		},
		Unit.Team.Blue: {
			Lane.Left: $RTop.position,
			Lane.Right: $RBot.position
		}
	}
	
	py_bridge.start_process()
	
	red_tower.died.connect(endscreen.show_end_screen.bind(false))
	blue_tower.died.connect(endscreen.show_end_screen.bind(true))


func spawn_unit(type: Unit.Type, team: Unit.Team, lane: Lane):
	# initiate unit
	var u: Unit = units_lib[type].instantiate()
	
	unit_bucket.add_child(u)
	u.spawn_and_setup(team, positions_lib[team][lane] as Vector2)

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta: float) -> void:
	pass#$Server1Debug.text = "connection " + str($P1Pose.camera_data[0]["server"].is_connection_available() if "ok" else "lost")
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
	
	
#func _on_p_1_pose_pose_changed(camera_id: int, pose: String) -> void:
	#$Pose1Debug.text = "Player 1 did: " + pose


func _on_p_1_pose_mask_updated(camera_id: int, texture: ImageTexture) -> void:
	var image = texture.get_image()
	var data = image.get_data()
	if camera_id == 0:
		$Mask1.texture = texture
	else:
		$Mask2.texture = texture


func _on_poses_completed_exercise(player: int, exercise: PoseServer.Exercise, left_lane: bool) -> void:
	var team: Unit.Team = Unit.Team.Red if player == 0 else Unit.Team.Blue
	var lane: Lane = Lane.Left if left_lane else Lane.Right
	
	# determine unit type based on exercise
	var type: Unit.Type
	match exercise:
		PoseServer.Exercise.SQUAT:
			type = Unit.Type.ARCHER
		PoseServer.Exercise.JJ:
			type = Unit.Type.WARRIOR
		PoseServer.Exercise.PUSH_UP:
			type = Unit.Type.LANCER
		PoseServer.Exercise.KNEE_UP:
			type = Unit.Type.MONK
		PoseServer.Exercise.LUNGE:
			type = Unit.Type.PAWN
	
	spawn_unit(type, team, lane)

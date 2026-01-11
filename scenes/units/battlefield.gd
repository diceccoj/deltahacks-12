extends Node2D
class_name Battlefield

@onready var red_tower: Tower = $RedTower
@onready var blue_tower: Tower = $BlueTower
@onready var unit_bucket: Node = $UnitBucket

@onready var red_start_pos: Marker2D = $LMid
@onready var blue_start_pos: Marker2D = $RMid

enum Lane {Left, Right}

var units_lib : Dictionary[Unit.Type, PackedScene] = {
	Unit.Type.WARRIOR: preload("uid://b345cshf836o5"),
	Unit.Type.ARCHER: preload("uid://bknltwirfyy0p"),
	Unit.Type.PAWN: preload("uid://dnf5n13sfx2hp"),
	Unit.Type.LANCER: preload("uid://d28gvfh66epf4")
	#Unit.Type.MONK: preload("uid://clpn1t4f5kxh2"), may not be needed
}

var positions_lib: Dictionary[Unit.Team, Dictionary]


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
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
	


func spawn_unit(type: Unit.Type, team: Unit.Team, lane: Lane):
	# initiate unit
	var u : Unit = units_lib[type].instantiate()
	
	unit_bucket.add_child(u)
	u.spawn_and_setup(team, positions_lib[team][lane] as Vector2)

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta: float) -> void:
	pass#$Server1Debug.text = str($P1Pose.server.is_connection_available())


func _on_p_1_pose_pose_changed(pose: String) -> void:
	$Pose1Debug.text = "Player 1 did: " + pose

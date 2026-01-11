extends Node2D
class_name Battlefield

@onready var red_tower: Tower = $RedTower
@onready var blue_tower: Tower = $BlueTower
@onready var unit_bucket: Node = $UnitBucket

@onready var red_start_pos: Marker2D = $LMid
@onready var blue_start_pos: Marker2D = $RMid

var units_lib : Dictionary[Unit.Type, PackedScene] = {
	Unit.Type.WARRIOR: preload("uid://b345cshf836o5"),
	Unit.Type.ARCHER: preload("uid://bknltwirfyy0p"),
	Unit.Type.PAWN: preload("uid://dnf5n13sfx2hp"),
	Unit.Type.LANCER: preload("uid://d28gvfh66epf4")
	#Unit.Type.MONK: preload("uid://clpn1t4f5kxh2"), may not be needed
}


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


func spawn_unit(type: Unit.Type, team: Unit.Team):
	# initiate unit
	var u : Unit = units_lib[type].instantiate()
	unit_bucket.add_child(u)
	
	# decide spawn conditions for unit
	var start_pos : Vector2
	match team: 
		Unit.Team.Red: start_pos = red_start_pos.position
		_: start_pos = blue_start_pos.position
		
	u.spawn_and_setup(team, start_pos)

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta: float) -> void:
	$Server1Debug.text = str($P1Pose.server.is_connection_available())


func _on_p_1_pose_pose_changed(pose: String) -> void:
	$Pose1Debug.text = "Player 1 did: " + pose

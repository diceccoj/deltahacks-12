extends Node

var old_pose : String = "?"
var cur_pose : String = "?"
var server: UDPServer

signal pose_changed(pose: String)

func _ready() -> void:
	server = UDPServer.new()
	server.listen(4242)

func _process(_delta: float) -> void:
	server.poll()
	if server.is_connection_available():
		var peer = server.take_connection()
		var frame_data = peer.get_packet()
		var pose = frame_data.get_string_from_utf8()
		if pose != cur_pose:
			old_pose = cur_pose
			cur_pose = pose
			pose_changed.emit(pose)

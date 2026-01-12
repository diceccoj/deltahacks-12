extends Node
class_name PyBridge

@export var python_file =  "res://python/main.py"
@export var mask_container : Control

@export var poses_server: PoseServer
@export var use_venv : bool

var user_terminal = ""
var python_cmnd_string : String
var process_id : int = -1



func _ready() -> void:
	pass

# start the window
func start_process() -> void:
	match (OS.get_name()):
		"Linux", "macOS":
			python_cmnd_string = "cd " + ProjectSettings.globalize_path("res://").replace(" ", "\\ ") +  (" && .venv/bin/python " if use_venv else " && python ") + python_file.trim_prefix("res://")
			process_id = OS.create_process("bash", ["-c", python_cmnd_string])
		"Windows":
			python_cmnd_string = "cd " + ProjectSettings.globalize_path("res://").replace(" ", "\\ ") +  (" && .venv\\Scripts\\python " if use_venv else " && python ") + python_file.trim_prefix("res://").replace("/", "\\")
			process_id = OS.execute("cmd.exe", ["/c", python_cmnd_string])
		_:
			push_error("Unrecognized OS!")
	print(python_cmnd_string)
	# prepare poses server
	poses_server.masks = mask_container
	poses_server.start_server()

func close_process():
	if (process_id > 0): OS.kill(process_id)
	
func _exit_tree() -> void:
	print("Process closed!")
	close_process()

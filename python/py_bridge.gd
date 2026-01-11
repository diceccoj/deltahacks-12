extends Node
class_name PyBridge

@export var python_file =  "res://python/main.py"

var user_terminal = ""
var python_cmnd_string : String
var process_id : int = -1

func _ready() -> void:
	# create python execution command
	python_cmnd_string = "cd " + ProjectSettings.globalize_path("res://").replace(" ", "\\ ") +  " && .venv/bin/python " + python_file.trim_prefix("res://")

# start the window
func start_process() -> void:
	match (OS.get_name()):
		"Linux", "macOS":
			process_id = OS.create_process("bash", ["-c", python_cmnd_string])
		"Windows":
			process_id = OS.execute("cmd.exe", ["/c", python_cmnd_string])
		_:
			push_error("Unrecognized OS!")

func close_process():
	if (process_id > 0): OS.kill(process_id)
	
func _exit_tree() -> void:
	print("Process closed!")
	close_process()

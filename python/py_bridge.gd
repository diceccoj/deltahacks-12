extends Node
class_name PyBridge

@export var python_file =  "res://python/main.py"
@export var open_console = false

var user_terminal = ""

func _ready() -> void:
	# determine user console
	if (open_console):
		var os_name := OS.get_name()

		match os_name:
			"Windows":
				user_terminal = "CMD.exe"
			"macOS":
				user_terminal = "x-term"
			"Linux":
				# just gonna pretend only gnome terminal exists
				user_terminal = "gnome-terminal"
			_:
				push_error("Unsupported OS: " + os_name)

func start_process() -> PackedStringArray:
	var output : PackedStringArray = []
	var cmnd_result : int = -100
	
	if (!open_console):
		var cmnd : PackedStringArray = ["env/bin/python", python_file]
		var cmnd_head = cmnd[0]
		cmnd.remove_at(0)
		cmnd_result = OS.execute(cmnd_head, cmnd, output, false)
	else:
		# MacOS needs a special case where it has bonus arguments at beginning to enable console
		if (user_terminal == "x-term"):
			var cmnd = ["-a", "Terminal", "env/bin/python"]
			cmnd_result = OS.execute("open", cmnd, output, false)
		
	return output

extends Node
class_name PoseServer

const array_size = 5
var poses : Array = ["?"]
var previous_frame_pose = "?"
var server: UDPServer
var seconds = 0
var time = 0

signal pose_changed(pose: String)
signal exercise_detected(exercise: String)

func _ready() -> void:
	server = UDPServer.new()
	server.listen(4242)
	exercise_detected.connect(my_awesome_function)

func my_awesome_function(pose: String):
	print(pose)

func _process(_delta: float) -> void:
	server.poll()
	
	# Keeps track of time
	time = time + 1
		
	if server.is_connection_available():
		var peer = server.take_connection()
		var frame_data = peer.get_packet()
		var pose = frame_data.get_string_from_utf8()
		
		# Check if the new pose is different from the first element
		if pose == previous_frame_pose && pose != poses[0]:
			# Insert new pose at the beginning
			poses.insert(0, pose)
			
			# Cap the array size at 10
			if poses.size() > array_size:
				poses.resize(array_size)
			
			pose_changed.emit(pose)
			
			if time > 15:
				# Check for completed exercises
				check_for_exercises()
		else:
			previous_frame_pose = pose

func check_for_exercises() -> void:
	# Define exercise pairs: [start_pose, end_pose, exercise_name]
	var exercise_pairs = [
		["standing", "squat", "squat", "jumping_jacks_closed"],
		["standing", "lunge", "lunge", "jumping_jacks_closed"],
		["jumping_jacks_closed", "jumping_jacks_open", "jumping jack"],
		["push_up", "push_up_down", "push up"]
	]
	
	# Loop through each exercise pair
	for pair in exercise_pairs:
		var exercise_name = pair[2]
		var end_pose = pair[1]
		var start_pose = pair[0]
		var alt_start_pose
		if pair.size() == 4:
			alt_start_pose = pair[3]
		else:
			alt_start_pose = start_pose
		
		# Check if the newest pose matches the start pose
		if poses[0] == start_pose || poses[0] == alt_start_pose:
			# Loop through the rest of the array to find the corresponding end pose
			for i in range(1, poses.size()):
				if poses[i] == end_pose:
					exercise_detected.emit(exercise_name)
					time = 0
					return  # Exit after detecting one exercise

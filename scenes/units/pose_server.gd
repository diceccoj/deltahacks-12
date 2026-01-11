extends Node
class_name PoseServer

const array_size = 5

# Separate state for each camera
var camera_data = {
	0: {
		"poses": ["?"],
		"previous_frame_pose": "?",
		"server": null,
		"mask_server": null,
		"time": 0
	},
	1: {
		"poses": ["?"],
		"previous_frame_pose": "?",
		"server": null,
		"mask_server": null,
		"time": 0
	}
}

# Signals now include camera_id
signal pose_changed(camera_id: int, pose: String)
signal exercise_detected(camera_id: int, exercise: String)
signal mask_updated(camera_id: int, texture: ImageTexture)


func _ready() -> void:
	# Create server for camera 0 (port 4242)
	camera_data[0]["server"] = UDPServer.new()
	camera_data[0]["server"].listen(4242)
	
	# Create server for camera 1 (port 4243)
	camera_data[1]["server"] = UDPServer.new()
	camera_data[1]["server"].listen(4243)
	
	camera_data[0]["mask_server"] = UDPServer.new()
	camera_data[0]["mask_server"].listen(4342)
	
	camera_data[1]["mask_server"] = UDPServer.new()
	camera_data[1]["mask_server"].listen(4343)
	
	exercise_detected.connect(my_awesome_function)
	
	print("Listening on ports 4242 (Camera 0) and 4243 (Camera 1)")

func my_awesome_function(camera_id: int, pose: String):
	print("Camera ", camera_id, ": ", pose)

func _process(_delta: float) -> void:
	# Process both cameras
	process_camera(0)
	process_camera(1)

func process_camera(camera_id: int) -> void:
	var data = camera_data[camera_id]
	var server = data["server"]
	
	server.poll()
	
	# Keeps track of time
	data["time"] += 1
		
	if server.is_connection_available():
		var peer = server.take_connection()
		var frame_data = peer.get_packet()
		var pose = frame_data.get_string_from_utf8()
		
		# Check if the new pose is different from the first element
		if pose == data["previous_frame_pose"] && pose != data["poses"][0]:
			# Insert new pose at the beginning
			data["poses"].insert(0, pose)
			
			# Cap the array size
			if data["poses"].size() > array_size:
				data["poses"].resize(array_size)
			
			pose_changed.emit(camera_id, pose)
			
			if data["time"] > 15:
				# Check for completed exercises
				check_for_exercises(camera_id)
		else:
			data["previous_frame_pose"] = pose
	
	var mask_server = data["mask_server"]
	mask_server.poll()
	
	if mask_server.is_connection_available():
		var peer = mask_server.take_connection()
		var packet = peer.get_packet()
		if packet.size() > 8:
			var header = packet.slice(0, 4).get_string_from_ascii()
			if header == "MASK":
				var image_data = packet.slice(8)
				var image = Image.new()
				var error = image.load_png_from_buffer(image_data)
				if error == OK:
					var texture = ImageTexture.create_from_image(image)
					data["mask_texture"] = texture
					mask_updated.emit(camera_id, texture)



func check_for_exercises(camera_id: int) -> void:
	var data = camera_data[camera_id]
	var poses = data["poses"]
	
	# Define exercise pairs: [start_pose, end_pose, exercise_name, alt_start_pose (optional)]
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
					exercise_detected.emit(camera_id, exercise_name)
					data["time"] = 0
					return  # Exit after detecting one exercise

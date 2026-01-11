extends Node
class_name PoseServer

@onready var particles := $"../Particles"

enum Exercise {
	SQUAT,
	JJ,
	PUSH_UP,
	LUNGE,
	KNEE_UP
}

@onready var p1_meter_gui: Dictionary[Exercise, ExerciseMeter] = {
	Exercise.SQUAT: $"../P1Meter/Squat",
	Exercise.JJ: $"../P1Meter/JJ",
	Exercise.PUSH_UP: $"../P1Meter/PushUp",
	Exercise.LUNGE: $"../P1Meter/Lunge",
	Exercise.KNEE_UP: $"../P1Meter/KneeUp"
}

@onready var p2_meter_gui: Dictionary[Exercise, ExerciseMeter] = {
	Exercise.SQUAT: $"../P2Meter/Squat",
	Exercise.JJ: $"../P2Meter/JJ",
	Exercise.PUSH_UP: $"../P1Meter/PushUp",
	Exercise.LUNGE: $"../P2Meter/Lunge",
	Exercise.KNEE_UP: $"../P2Meter/KneeUp"
}

const MAX_SQUAT_TIME = 1.5
const MAX_JJ_COUNT = 14
const MAX_PU_COUNT = 2
const MAX_LUNGE_TIME = 2
const MAX_KU_COUNT = 9

var state_template := {
	"squat_ready": false,
	"jj_ready": false,
	"pu_ready": false,
	"lunge_ready": false,
	"ku_ready": false,
	
	"squat_time": 0,
	"jj_count": 0,
	"jj_did_one": false,
	"pu_count": 0,
	"pu_did_one": false,
	"lunge_time": 0,
	"ku_count": 0,
	"ku_did_one": false
}

var player_state = [state_template.duplicate_deep(), state_template.duplicate_deep()]

signal completed_exercise(player: int, exercise: Exercise, left_lane: bool)
	

const array_size = 5

# Separate state for each camera
var camera_data = {
	0: {
		"poses": ["?"],
		"previous_frame_pose": "?",
		"server": null,
		"mask_server": null,
		"time": 0,
		"current_pose": "?"
	},
	1: {
		"poses": ["?"],
		"previous_frame_pose": "?",
		"server": null,
		"mask_server": null,
		"time": 0,
		"current_pose": "?"
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

func _process(delta: float) -> void:
	# Process both cameras
	process_camera(0)
	process_camera(1)
	check_for_exercises(0, delta)
	check_for_exercises(1, delta)

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
		
		data["current_pose"] = pose
		
		# Check if the new pose is different from the first element
		if pose == data["previous_frame_pose"] && pose != data["poses"][0]:
			# Insert new pose at the beginning
			data["poses"].insert(0, pose)
			
			# Cap the array size
			if data["poses"].size() > array_size:
				data["poses"].resize(array_size)
			
			pose_changed.emit(camera_id, pose)
			
			#if data["time"] > 15:
				## Check for completed exercises
				#check_for_exercises(camera_id)
		else:
			data["previous_frame_pose"] = pose
	
	var mask_server = data["mask_server"]
	mask_server.poll()
	
	if mask_server.is_connection_available():
		var peer = mask_server.take_connection()
		var packet = peer.get_packet()
		if packet.size() > 8:
			var header = packet.slice(0, 4).get_string_from_ascii()
			var image_data = packet.slice(8)
			var image = Image.new()
			var error = image.load_jpg_from_buffer(image_data)
			if error == OK:
				var texture = ImageTexture.create_from_image(image)
				data["mask_texture"] = texture
				mask_updated.emit(camera_id, texture)


func check_for_exercises(camera_id: int, delta: float) -> void:
	var data = camera_data[camera_id]
	var poses = data["poses"]
	
	# exercise protocols:
		# squat: fill meter continuously while squatting, max out at 2 seconds
		# jjs: fill meter when alternating between jj open and close, 20 times
	var state = player_state[camera_id]
	var gui := p1_meter_gui if camera_id == 0 else p2_meter_gui
	var pose: String = data["current_pose"]
	#print(camera_id, " ", pose)
	
	var mask_pos = $"../Mask1".position + $"../Mask1".size / 2 if camera_id == 0 else $"../Mask2".position + $"../Mask2".size / 2
	
	if (camera_id == 0 and not Input.is_key_pressed(KEY_SHIFT)) or (camera_id == 1 and Input.is_key_pressed(KEY_SHIFT)):
		if Input.is_key_pressed(KEY_A):
			pose = "place_left"
		elif Input.is_key_pressed(KEY_S):
			pose = "place_right"
		elif Input.is_key_pressed(KEY_D):
			pose = "squat"
		elif Input.is_key_pressed(KEY_F):
			pose = "jumping_jacks_open"
		elif Input.is_key_pressed(KEY_G):
			pose = "jumping_jacks_closed"
		elif Input.is_key_pressed(KEY_H):
			pose = "push_up_down"
		elif Input.is_key_pressed(KEY_J):
			pose = "push_up"
		elif Input.is_key_pressed(KEY_K):
			pose = "knee_up_l"
		elif Input.is_key_pressed(KEY_L):
			pose = "knee_up_r"
		elif Input.is_key_pressed(KEY_Z):
			pose = "right lunge"
		elif Input.is_key_pressed(KEY_X):
			pose = "left lunge"
	
	var launch_particles = func(ex, amt):
		var start_pos = mask_pos
		var end_pos = gui[ex].global_position + gui[ex].size
		particles.launch(start_pos, end_pos, amt)

	
	if pose == "squat":
		state["squat_time"] += delta
		gui[Exercise.SQUAT].set_progress(clamp(state["squat_time"] / MAX_SQUAT_TIME, 0, 1))
		launch_particles.call(Exercise.SQUAT, 1)
		if state["squat_time"] > MAX_SQUAT_TIME:
			state["squat_ready"] = true
			gui[Exercise.SQUAT].set_readied(true)
	else:
		if not state["squat_ready"]:
			state["squat_time"] = max(0, state["squat_time"] - delta)
			gui[Exercise.SQUAT].set_progress(clamp(state["squat_time"] / MAX_SQUAT_TIME, 0, 1))
	
	if pose == "right lunge" or pose == "left lunge":
		state["lunge_time"] += delta
		gui[Exercise.LUNGE].set_progress(clamp(state["lunge_time"] / MAX_LUNGE_TIME, 0, 1))
		launch_particles.call(Exercise.LUNGE, 1)
		if state["lunge_time"] > MAX_LUNGE_TIME:
			state["lunge_ready"] = true
			gui[Exercise.LUNGE].set_readied(true)
	else:
		if not state["lunge_ready"]:
			state["lunge_time"] = max(0, state["lunge_time"] - delta)
			gui[Exercise.LUNGE].set_progress(clamp(state["lunge_time"] / MAX_LUNGE_TIME, 0, 1))
	
	
	if (pose == "jumping_jacks_open" and !state["jj_did_one"]) \
		or ((pose == "standing" or pose == "jumping_jacks_closed") and state["jj_did_one"]):
		state["jj_did_one"] = !state["jj_did_one"]
		state["jj_count"] += 1
		print("DID JJ ", pose, " ", state["jj_count"])
		launch_particles.call(Exercise.JJ, 5)
		gui[Exercise.JJ].set_progress(clamp(float(state["jj_count"]) / MAX_JJ_COUNT, 0, 1))
		if state["jj_count"] > MAX_JJ_COUNT:
			state["jj_ready"] = true
			gui[Exercise.JJ].set_readied(true)
		
	if (pose == "push_up" and !state["pu_did_one"]) or (pose == "push_up_down" and state["pu_did_one"]):
		state["pu_did_one"] = !state["pu_did_one"]
		state["pu_count"] += 1
		print("DID PU ", pose, " ", state["pu_count"], " ", state["pu_did_one"])
		launch_particles.call(Exercise.PUSH_UP, 15)
		gui[Exercise.PUSH_UP].set_progress(clamp(float(state["pu_count"]) / MAX_PU_COUNT, 0, 1))
		if state["pu_count"] >= MAX_PU_COUNT:
			state["pu_ready"] = true
			gui[Exercise.PUSH_UP].set_readied(true)
			
	if (pose == "knee_up_l" and !state["ku_did_one"]) or (pose == "knee_up_r" and state["ku_did_one"]):
		state["ku_did_one"] = !state["ku_did_one"]
		state["ku_count"] += 1
		launch_particles.call(Exercise.KNEE_UP, 5)
		gui[Exercise.KNEE_UP].set_progress(clamp(float(state["ku_count"]) / MAX_KU_COUNT, 0, 1))
		if state["ku_count"] >= MAX_KU_COUNT:
			state["ku_ready"] = true
			gui[Exercise.KNEE_UP].set_readied(true)
	
	## SEEND IT!
	if pose == "place_left" || pose == "place_right":
		var d := [
			["squat_ready", Exercise.SQUAT],
			["jj_ready", Exercise.JJ],
			["pu_ready", Exercise.PUSH_UP],
			["lunge_ready", Exercise.LUNGE],
			["ku_ready", Exercise.KNEE_UP]
		]
		for p in d:
			var s: String = p[0]
			var ex: Exercise = p[1]
			if state[s]: # ready
				completed_exercise.emit(camera_id, ex, pose == "place_left")
				state[s] = false
				gui[ex].set_progress(0)
				gui[ex].set_readied(false)
				
				if ex == Exercise.SQUAT:
					state["squat_time"] = 0
				elif ex == Exercise.JJ:
					state["jj_count"] = 0
					state["jj_did_one"] = false
				elif ex == Exercise.PUSH_UP:
					state["pu_count"] = 0
					state["pu_did_one"] = false
				elif ex == Exercise.LUNGE:
					state["lunge_time"] = 0
				elif ex == Exercise.KNEE_UP:
					state["ku_count"] = 0
					state["ku_did_one"] = false
	
	
	# Define exercise pairs: [start_pose, end_pose, exercise_name, alt_start_pose (optional)]
	#var exercise_pairs = [
		#["standing", "squat", "squat", "jumping_jacks_closed"],
		#["standing", "lunge", "lunge", "jumping_jacks_closed"],
		#["jumping_jacks_closed", "jumping_jacks_open", "jumping jack"],
		#["push_up", "push_up_down", "push up"]
	#]
	#
	## Loop through each exercise pair
	#for pair in exercise_pairs:
		#var exercise_name = pair[2]
		#var end_pose = pair[1]
		#var start_pose = pair[0]
		#var alt_start_pose
		#if pair.size() == 4:
			#alt_start_pose = pair[3]
		#else:
			#alt_start_pose = start_pose
		#
		## Check if the newest pose matches the start pose
		#if poses[0] == start_pose || poses[0] == alt_start_pose:
			## Loop through the rest of the array to find the corresponding end pose
			#for i in range(1, poses.size()):
				#if poses[i] == end_pose:
					#exercise_detected.emit(camera_id, exercise_name)
					#data["time"] = 0
					#return  # Exit after detecting one exercise

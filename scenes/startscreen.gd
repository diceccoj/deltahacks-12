extends Control

@onready var start_button: TextureButton = $StartButton
@onready var fade_animation: ColorRect = $"../FadeAnimation"


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.

var button_type = null

# Run the game on start press 
func _on_start_button_pressed() -> void:
	button_type = "start" 
	$"../FadeAnimation".show()
	$"../FadeAnimation/FadeTimer".start()
	$"../FadeAnimation/AnimationPlayer".play("fadein")


func _on_fade_timer_timeout() -> void:
	if button_type == "start":
		get_tree().change_scene_to_file("res://scenes/units/battlefield.tscn") #Put the game start state here
		$"../FadeAnimation/AnimationPlayer".play("fadeout")
		# Note, you will have to include $"../FadeAnimation/AnimationPlayer".play("fadeout")  on _func ready for the scene in which you are going to

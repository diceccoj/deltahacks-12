extends Control
class_name Endscreen

@onready var overlay := $Blackscreen
@onready var red_wins := $RedTeamWins
@onready var blue_wins := $BlueTeamWins
@onready var scroll := $Scroll
@onready var play_again := $PlayAgainButton
@onready var fade_animation: ColorRect = $"../FadeAnimation"

var button_type = null

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	visible = false

	overlay.visible = false
	red_wins.visible = false
	blue_wins.visible = false
	
func _input(event: InputEvent) -> void:
	if event.is_action_pressed("debug_red_win"):
		show_end_screen(true)

	if event.is_action_pressed("debug_blue_win"):
		show_end_screen(false)

func show_end_screen(winning_team_red: bool) -> void:
	visible = true

	overlay.visible = true
	scroll.visible = true
	play_again.visible = true

	# Hide both first
	red_wins.visible = false
	blue_wins.visible = false

	if winning_team_red == true:
		red_wins.visible = true
	elif winning_team_red == false:
		blue_wins.visible = true




func _on_fade_timer_timeout() -> void: #Make this the start screen
	# Same note, you'll have to link fade in and play it on the new scene
	if button_type == "replay":
		get_tree().change_scene_to_file("res://scenes/units/battlefield.tscn") #Put the game start state here
		$"../FadeAnimation/AnimationPlayer".play("fadeout")
		# Note, you will have to include $"../FadeAnimation/AnimationPlayer".play("fadeout")  on _func ready for the scene in which you are going to

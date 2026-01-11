extends Control

@onready var overlay := $Blackscreen
@onready var red_wins := $RedTeamWins
@onready var blue_wins := $BlueTeamWins
@onready var scroll := $Scroll
@onready var play_again := $PlayAgain

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	visible = false

	overlay.visible = false
	red_wins.visible = false
	blue_wins.visible = false
	scroll.visible = false
	play_again.visible = false
	
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


# Replace with reset to start of game state
func _on_play_again_pressed() -> void: 
	pass # Replace with function body.

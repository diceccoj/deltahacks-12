extends Node
class_name CouchPotato

# if you ever wanna play the game without moving (DEV ONLY)

@export var battlefield : Battlefield

var timer : Timer

var type_odds = {
	Unit.Type.ARCHER: 0.25,
	Unit.Type.WARRIOR: 0.25,
	Unit.Type.LANCER: 0.25,
	Unit.Type.PAWN: 0.25
}

var team_odds = {
	Unit.Team.Red: 0.5,
	Unit.Team.Blue: 0.5
}
var lane_odds = {
	Battlefield.Lane.Left: 0.5,
	Battlefield.Lane.Right: 0.5
}


func _ready() -> void:
	timer = Timer.new()
	add_child(timer)
	timer.wait_time = 5
	timer.timeout.connect(execute)
	timer.start()

func execute():
	
	var rng = RandomNumberGenerator.new()
	
	var u_type = type_odds.keys()[rng.rand_weighted(type_odds.values())]
	var u_team = team_odds.keys()[rng.rand_weighted(team_odds.values())]
	var u_lane = lane_odds.keys()[rng.rand_weighted(lane_odds.values())]
	battlefield.spawn_unit(u_type, u_team, u_lane)
	
	timer.start()

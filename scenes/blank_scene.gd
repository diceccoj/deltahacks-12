extends Node2D

@onready var py_bridge: PyBridge = $PyBridge


func _ready() -> void:
	py_bridge.start_process()

#func _process(delta: float) -> void:

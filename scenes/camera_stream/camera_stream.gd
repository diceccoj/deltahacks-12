extends TextureRect

@onready var endscreen: Control = $Endscreen
var server: UDPServer

'''
jonathan note:
	Didn't look like most of this code did anything anymore
	I just commented them for now. If i'm right pls delete
'''


func _ready() -> void:
	pass
	#server = UDPServer.new()
	#server.listen(4242)

func _process(_delta: float) -> void:
	'''
	server.poll()
	if server.is_connection_available():
		var peer = server.take_connection()
		var frame_data = peer.get_packet()
		var image = _decode_image(frame_data)
		texture = ImageTexture.create_from_image(image)
	'''

extends Node2D

@export var arc_height: float = -200.0  # Perpendicular offset from straight line
@export var particle_lifetime: float = 1.5
@export var particle_color: Color = Color.WHITE
@export var particle_size: float = 4.0

var particles: Array[Dictionary] = []

func _ready():
	pass

# Quadratic bezier curve interpolation
func bezier_quadratic(p0: Vector2, p1: Vector2, p2: Vector2, t: float) -> Vector2:
	var u = 1.0 - t
	return u * u * p0 + 2.0 * u * t * p1 + t * t * p2

# Calculate control point perpendicular to the line between start and end
func get_control_point(start, end, arc) -> Vector2:
	var midpoint = (start + end) * 0.5
	var direction = (end - start).normalized()
	var perpendicular = Vector2(-direction.y, direction.x)  # Rotate 90 degrees
	return midpoint + perpendicular * arc

func launch(start, end, count):
	#particles.clear()
	
	# Create particle data
	for i in range(count):
		var particle = {
			"start": start,
			"end": end,
			"progress": 0.0,
			"speed": randf_range(0.6, 1.4) * 3.0,  # Slight variation in speed
			"lifetime": particle_lifetime,
			"size": particle_size * randf_range(0.7, 1.3),
			"alpha": 1.0,
			"arc_height" : (arc_height + randf_range(-20, 20)) * -sign(start.x - end.x)
		}
		particles.append(particle)
	
	queue_redraw()

func _process(delta: float):
	if particles.is_empty():
		return
	
	var active_particles = false
	
	for particle in particles:
		particle.progress += delta * particle.speed / particle.lifetime
		
		# Fade out near the end
		if particle.progress > 0.8:
			particle.alpha = (1.0 - particle.progress) * 5.0
		
		if particle.progress < 1.0:
			active_particles = true
	
	# Remove completed particles
	if not active_particles:
		particles.clear()
	
	queue_redraw()

func _draw():
	if particles.is_empty():
		return
	
	for particle in particles:
		if particle.progress >= 1.0:
			continue
		
		var start = particle["start"]
		var end = particle["end"]
		var ctrl = get_control_point(start, end, particle["arc_height"])
		# Calculate position along bezier curve
		var pos = bezier_quadratic(start, ctrl, end, particle.progress)
		
		# Draw particle
		var color = particle_color
		color.a = particle.alpha
		draw_circle(pos, particle.size, color)
		
		# Optional: draw a small trail
		if particle.progress > 0.05:
			var prev_pos = bezier_quadratic(start, ctrl, end, particle.progress - 0.05)
			color.a *= 0.3
			draw_line(prev_pos, pos, color, particle.size * 0.5)

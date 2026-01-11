shader_type canvas_item;

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	// If pixel is black (r < 0.5), make it 30% transparent
	if (tex.r < 0.5) {
		COLOR = vec4(tex.rgb, 0.3);
	} else {
		COLOR = tex;
	}
}
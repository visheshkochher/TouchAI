
// phong1GLSLVertexMAC ------------------------------------------------------
// Metal / macOS port of phong1GLSLVertex + phong1GLSLGeometry.
// Metal has no geometry shader stage, so the point -> billboard-quad
// expansion that used to live in phong1GLSLGeometry is done here instead:
// renderParticles/grid1 is now a 2x2 quad (P.xy spans [-0.5, 0.5]) copied
// once per particle, and every vertex offsets itself in camera space.
// Math is a 1:1 port of the geometry shader - do not "simplify".

uniform vec2 uParticleSizeVariance;
uniform vec2 uLifeFade;
uniform float uFaceCam;

uniform int uParticlesPerInstance;
uniform vec4 uMapSize; // contains (1 / w, 1 / h, w, h)
uniform sampler2D sPosition;
uniform sampler2D sSize;
uniform sampler2D sLife;
uniform sampler2D sRotation;

in float objIndex;

out Vertex {
	vec4 color;
	vec2 texCoord0;
	flat uint instanceID;
}vVerts;

float reMap(in float value, in float low1, in float high1, in float low2, in float high2){
	return float(low2 + (value - low1) * (high2 - low2) / (high1 - low1));
}

mat4 rotationX( in float angle ) {
	return mat4(	1.0,		0,			0,			0,
			 		0, 	cos(angle),	-sin(angle),		0,
					0, 	sin(angle),	 cos(angle),		0,
					0, 			0,			  0, 		1);
}

mat4 rotationY( in float angle ) {
	return mat4(	cos(angle),		0,		sin(angle),	0,
					        0,		1.0,			 0,	0,
					-sin(angle),	0,		cos(angle),	0,
							0, 		0,				0,	1);
}

mat4 rotationZ( in float angle ) {
	return mat4(	cos(angle),		-sin(angle),	0,	0,
			 		sin(angle),		cos(angle),		0,	0,
							0,				0,		1,	0,
							0,				0,		0,	1);
}

void main()
{
	int partIndex = TDInstanceID() * uParticlesPerInstance + int(objIndex);
	vVerts.instanceID = uint(partIndex);

	int rowX = partIndex % int(uMapSize.z);
	int rowY = partIndex / int(uMapSize.z);

	vec2 posUV = vec2((float(rowX) + 0.5) * uMapSize.x,
						(float(rowY) + 0.5) * uMapSize.y);

	// P.xy is the quad corner in [-0.5, 0.5]; it replaces the geometry
	// shader's four EmitVertex() calls and its hard-coded texCoord0.
	vec2 corner = P.xy;
	vVerts.texCoord0 = corner + vec2(0.5);

	vec4 life = texture(sLife, posUV);
	vec4 positionOffset = texture(sPosition, posUV);

	if (life.g <= 0.0)
	{
		// Dead particle: park the whole quad outside the clip volume. The
		// geometry shader used to just skip EmitVertex() for these.
		gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
		vVerts.color = vec4(0.0);
		return;
	}

	float scale = texture(sSize, posUV).r;
	float particle_size = uParticleSizeVariance.x + scale * (uParticleSizeVariance.y - uParticleSizeVariance.x);
	vec3 angle = texture(sRotation, posUV).rgb;

	//Old Camera Space (Legacy 088 shaders)
	//vec4 camPos = uTDMat.worldCam * vec4(positionOffset.xyz, 1.0);
	vec4 camPos = uTDMats[0].worldCam * vec4(positionOffset.xyz, 1.0);

	vec4 vpos = vec4(camPos.xy + corner * particle_size, camPos.zw);
	if (uFaceCam == 0.0){
		vpos = camPos + vec4(corner * particle_size, vec2(0.0))
				* rotationX(angle.x) * rotationY(angle.y) * rotationZ(angle.z);
	}

	gl_Position = uTDMats[0].proj * vpos;

#ifndef TD_PICKING_ACTIVE

	vec4 color = TDInstanceColor(Cd);

	// apply fadein and fadeout
	float fadeIn = reMap(min(life.r-life.g,uLifeFade.x),0.0,uLifeFade.x,0.0,1.0);
	float fadeOut = reMap(min(life.g,uLifeFade.y),uLifeFade.y,0.0,0.0,1.0);
	float fade = fadeIn - fadeOut;

	color.a = mix(0.0,1.0,fade);
	vVerts.color = color;

#else // TD_PICKING_ACTIVE

	TDWritePickingValues();

#endif // TD_PICKING_ACTIVE
}

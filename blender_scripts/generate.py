import bpy
from math import radians, sqrt
import random
import os, sys


# Random seed
SEED = 0


# Directory for blend files and render results.
# PLEASE DOES NOT CHANGE THESE, THIS IS NOT SUPPORTED YET
BLEND_FILES_DIR = os.path.join('.', 'generated')
RENDER_DIR = os.path.join('.', 'renders')


# Number of different files to generate
NUM_RUNS = 2


# Output options. This includes file format (either jpeg or png), the frames per seconds, the number of
# seconds and the resolution of each frame
FILE_FORMAT = 'JPEG'
# FILE_FORMAT = 'PNG'
FPS = 30
NUM_FRAMES = 120
RENDER_RESOLUTION = 512


# Dirt level on camera screen. Should be an integer in [0, 10]
DIRT_LEVEL = 9


# Parameters about the spheroid
# Minimum and maximum rotation speeds, and number of changes in rotation axis
ROT_SPEED_MIN = 60
ROT_SPEED_MAX = 360
MAX_ROT_CHANGES = 4

# Spheroid's fall speed in the tube (essentially the speed at which dirt moves)
FALL_SPEED_MIN = 1
FALL_SPEED_MAX = 10

# Displacement strength bounds
DISPLACE_STR_MIN = 0.2
DISPLACE_STR_MAX = 2

# Displacement detail scale
CLOUDS_SCALE_MIN = 1
CLOUDS_SCALE_MAX = 2

# Density and color of the spheroid
SPHEROID_DENSITY = 2
SPHEROID_COLOR = (0.11, 0.11, 0.11, 1.0)



def create_spheroid_material(sphere):
	mat = bpy.data.materials.new(name='SpheroidMaterial')
	sphere.data.materials.append(mat)

	mat.use_nodes = True
	nodes = mat.node_tree.nodes
	links = mat.node_tree.links
	nodes.clear()
	node_vol = nodes.new(type='ShaderNodeVolumePrincipled')
	node_vol.location = (-600, 0)
	node_vol.inputs[0].default_value = SPHEROID_COLOR
	node_vol.inputs[2].default_value = SPHEROID_DENSITY
	node_out = nodes.new(type='ShaderNodeOutputMaterial')
	node_out.location = (0, 0)

	links.new(node_vol.outputs[0], node_out.inputs[1])

def create_screen_material(plane, fall_speed):
	mat = bpy.data.materials.new(name='ScreenMaterial')
	plane.data.materials.append(mat)

	mat.use_nodes = True
	nodes = mat.node_tree.nodes
	links = mat.node_tree.links
	nodes.clear()

	# Create the nodes
	coords = nodes.new(type='ShaderNodeTexCoord')
	mapping = nodes.new(type='ShaderNodeMapping')
	noise = nodes.new(type='ShaderNodeTexNoise')
	add = nodes.new(type='ShaderNodeMath')
	add.operation = 'ADD'
	power = nodes.new(type='ShaderNodeMath')
	power.operation = 'POWER'
	muladd = nodes.new(type='ShaderNodeMath')
	muladd.operation = 'MULTIPLY_ADD'
	value = nodes.new(type='ShaderNodeValue')
	inv = nodes.new(type='ShaderNodeInvert')
	bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
	out = nodes.new(type='ShaderNodeOutputMaterial')

	# Set the values
	bsdf.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
	bsdf.inputs[7].default_value = 0
	bsdf.inputs[9].default_value = 1
	inv.inputs[0].default_value = 1
	power.inputs[1].default_value = 100
	muladd.inputs[1].default_value = 0.01
	muladd.inputs[2].default_value = 0.7
	value.outputs[0].default_value = 10 - DIRT_LEVEL
	noise.inputs[2].default_value = 10
	noise.inputs[3].default_value = 2
	noise.inputs[4].default_value = 0.5
	noise.inputs[5].default_value = 0.5

	# Create connections
	links.new(coords.outputs[3], mapping.inputs[0])
	links.new(mapping.outputs[0], noise.inputs[0])
	links.new(value.outputs[0], muladd.inputs[0])
	links.new(noise.outputs[0], add.inputs[0])
	links.new(muladd.outputs[0], add.inputs[1])
	links.new(add.outputs[0], power.inputs[0])
	links.new(power.outputs[0], inv.inputs[1])
	links.new(inv.outputs[0], bsdf.inputs[21])
	links.new(bsdf.outputs[0], out.inputs[0])

	# Position nodes
	out.location = 			(0, 0)
	bsdf.location = 		(-420, 0)
	inv.location = 			(-900, 0)
	power.location = 		(-1260, 0)
	add.location = 			(-1560, 0)
	noise.location =		(-1980, 60)
	muladd.location = 		(-1980, -300)
	value.location = 		(-2340, -540)
	mapping.location = 		(-2520, 60)
	coords.location = 		(-2880, 60)

	# Mapping keyframes
	mapping_z = random.uniform(-100, 100)
	mapping.inputs[1].default_value = (0.0, 0.0, mapping_z)
	mapping.inputs[1].keyframe_insert(data_path='default_value', frame=1)
	mapping.inputs[1].default_value = (0.0, - fall_speed * (NUM_FRAMES / FPS), mapping_z)
	mapping.inputs[1].keyframe_insert(data_path='default_value', frame=NUM_FRAMES)

	# Make all the keyframes change linearly
	for fc in mat.node_tree.animation_data.action.fcurves:
		fc.extrapolation = 'LINEAR'
		for kp in fc.keyframe_points:
			kp.handle_left_type  = 'VECTOR'
			kp.handle_right_type = 'VECTOR'


def setup_compositor():
	scn = bpy.context.scene
	scn.use_nodes = True

	nodes = scn.node_tree.nodes
	links = scn.node_tree.links

	nodes.clear()
	links.clear()

	render = nodes.new(type='CompositorNodeRLayers')
	alpha = nodes.new(type='CompositorNodeAlphaOver')
	denoise = nodes.new(type='CompositorNodeDenoise')
	out = nodes.new(type='CompositorNodeComposite')

	links.new(render.outputs[0], denoise.inputs[0])
	links.new(denoise.outputs[0], alpha.inputs[2])
	links.new(alpha.outputs[0], out.inputs[0])

	out.location = 			(0, 0)
	alpha.location = 		(-420, 0)
	denoise.location = 		(-900, 0)
	render.location = 		(-1260, 0)




def create_blend_file(outfilename, rotspeed, rotchanges):
	# Clean the scene
	bpy.ops.wm.read_factory_settings(use_empty=True)
	scn = bpy.context.scene
	scn.render.resolution_x = RENDER_RESOLUTION
	scn.render.resolution_y = RENDER_RESOLUTION
	scn.render.engine = 'CYCLES'
	bpy.context.preferences.addons[
	    "cycles"
	].preferences.compute_device_type = "CUDA" # or "OPENCL"
	scn.cycles.device = 'GPU'
	scn.frame_end = NUM_FRAMES
	bpy.ops.world.new()
	world = bpy.data.worlds['World']
	world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
	scn.world = world
	scn.render.film_transparent = True
	scn.render.filepath = os.path.join("//", "..", RENDER_DIR, outfilename, "frame")
	scn.render.image_settings.color_mode = 'BW'
	scn.render.image_settings.file_format = FILE_FORMAT




	# Add an orthographic camera pointing in the Y direction
	cam = bpy.data.cameras.new("Camera")
	cam.type = 'ORTHO'
	camobj = bpy.data.objects.new("Camera", cam)
	camobj.location = (0, -5, 0)
	camobj.rotation_euler = (radians(90), 0, 0)
	scn.collection.objects.link(camobj)
	scn.camera = camobj

	# Add a plane and attach it to camera screen
	bpy.ops.mesh.primitive_plane_add()
	plane = bpy.data.objects['Plane']
	plane.location = (0, -4.9, 0)
	plane.rotation_euler = (radians(90), 0, 0)
	plane.scale = (3, 3, 1)
	plane.parent = camobj
	plane.matrix_parent_inverse = camobj.matrix_world.inverted()

	# Add an icosphere and parent it to camera
	bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3)
	sphere = bpy.data.objects['Icosphere']
	sphere.parent = camobj
	sphere.matrix_parent_inverse = camobj.matrix_world.inverted()

	# Give random rotation
	sphere.keyframe_insert(data_path='rotation_euler', frame=1)
	for i in range(rotchanges):
		rweig = (random.random(), random.random(), random.random())
		theta = random.random() * radians(rotspeed) * (NUM_FRAMES / FPS)
		sphere.rotation_euler = (rweig[0] * theta, rweig[1] * theta, rweig[2] * theta)
		sphere.keyframe_insert(data_path='rotation_euler', frame=int((i + 1) * NUM_FRAMES / rotchanges))

	# Add materials
	create_spheroid_material(sphere)
	create_screen_material(plane, random.uniform(FALL_SPEED_MIN, FALL_SPEED_MAX))


	# Add resolution
	ssmod = sphere.modifiers.new('SubDiv', 'SUBSURF')
	ssmod.levels = 5
	ssmod.render_levels = 5

	# Add the displacement
	dpmod = sphere.modifiers.new('Displace.001', 'DISPLACE')
	dpmod.strength = random.uniform(DISPLACE_STR_MIN, DISPLACE_STR_MAX)

	clouds = bpy.data.textures.new('DisplaceTex.001', 'CLOUDS')
	clouds.noise_scale = random.uniform(CLOUDS_SCALE_MIN, CLOUDS_SCALE_MAX)
	dpmod.texture = clouds

	# Modify the cloud texture using an empty object
	empty = bpy.data.objects.new("EmptyObject", None)
	scn.collection.objects.link(empty)
	dpmod.texture_coords = 'OBJECT'
	dpmod.texture_coords_object = empty
	empty.location = (random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))
	empty.parent = sphere
	empty.matrix_parent_inverse = sphere.matrix_world.inverted()


	# Add light
	bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))


	# Make all the keyframes change linearly
	for fc in sphere.animation_data.action.fcurves:
		fc.extrapolation = 'LINEAR'
		for kp in fc.keyframe_points:
			kp.handle_left_type  = 'VECTOR'
			kp.handle_right_type = 'VECTOR'


	# Setup the compositor
	setup_compositor()

	# Save the file
	outpath = "{0}/{1}.blend".format(BLEND_FILES_DIR, outfilename)
	outpath = os.path.abspath(outpath)
	bpy.ops.wm.save_as_mainfile(filepath=outpath)




if __name__ == '__main__':
	# Initialize script
	random.seed(SEED)

	# Create generated files directory
	if not os.path.exists(BLEND_FILES_DIR):
		os.makedirs(BLEND_FILES_DIR)
	elif not os.path.isdir(BLEND_FILES_DIR):
		raise Exception("Path {} already exists and it's not a directory".format(BLEND_FILES_DIR))

	# Create render directory
	if not os.path.exists(RENDER_DIR):
		os.makedirs(RENDER_DIR)
	elif not os.path.isdir(RENDER_DIR):
		raise Exception("Path {} already exists and it's not a directory".format(RENDER_DIR))


	# For each run create the file and the render directory
	for run in range(NUM_RUNS):
		run_name = "run{0:06d}".format(run)

		# Create render directory
		run_render_dir = os.path.join(RENDER_DIR, run_name)
		if not os.path.exists(run_render_dir):
			os.makedirs(run_render_dir)
		elif not os.path.isdir(run_render_dir):
			sys.stderr.write("Path {0} already exists and it's not a directory.{1}".format(run_render_dir, os.linesep))
			continue

		# Create blend file
		create_blend_file(run_name, random.uniform(ROT_SPEED_MIN, ROT_SPEED_MAX), random.randint(0, MAX_ROT_CHANGES))




	# create_blend_file("test", rotspeed=360, rotchanges=2)
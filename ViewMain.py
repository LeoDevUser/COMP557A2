#Leonardo Martinez 261082940
import moderngl as mgl
from pyglm import glm
from Scene import Scene, Camera

class ViewMain():
    def __init__(self, scene: Scene, camera: Camera, ctx: mgl.Context):
        self.scene = scene
        self.camera = camera
        self.ctx = ctx

    def paintGL(self, aspect_ratio: float):
        self.ctx.clear(0,0,0)
        self.ctx.enable(mgl.DEPTH_TEST)

        # set up projection and view matrix for the main camera vew
        fov = glm.radians(self.scene.controls.main_view_fov)
        self.camera.V = glm.translate(glm.mat4(1), glm.vec3(0, 0, -self.camera.distance)) * self.camera.R
        n,f = self.scene.compute_nf_from_view(self.camera.V)		
        self.camera.P = glm.perspective(fov, aspect_ratio, n, f)

        cam_mvp = self.camera.P * self.camera.V 
        cam_mv = self.camera.V 

        self.scene.prog_shadow_map['u_mv'].write(cam_mv)
        self.scene.prog_shadow_map['u_mvp'].write(cam_mvp)
        light_pos = self.scene.get_light_pos_in_view( self.camera.V )		 
        self.scene.prog_shadow_map['u_light_pos'].write(light_pos)
        self.scene.prog_shadow_map['u_use_lighting'] = True		
        self.scene.render_for_view()

        if self.scene.controls.cheap_shadows:
            ground_plane_in_world_coords = self.scene.get_ground_plane()
            light_pos_in_world_coords = self.scene.get_light_pos_in_world()

            L = light_pos_in_world_coords.xyz
            n = glm.normalize(ground_plane_in_world_coords.xyz)
            w = n

            #handle case where plane normal is nearly parallel to y-axis
            if abs(w.y) < 0.9:
                u = glm.normalize(glm.cross(glm.vec3(0, 1, 0), w))
            else: #normal nearly vertical, must use different vector
                u = glm.normalize(glm.cross(glm.vec3(1, 0, 0), w))

            v = glm.cross(w, u)

            #build V matrix - transforms from light's coordinate system to world
            V = glm.mat4(
                glm.vec4(u, 0),
                glm.vec4(v, 0),
                glm.vec4(w, 0),
                glm.vec4(L, 1)
            )

            point = ground_plane_in_world_coords.w * n
            d = glm.dot(n, (L-point))

            P = glm.mat4(
                d, 0, 0, 0,
                0, d, 0, 0,
                0, 0, d, -1,
                0, 0, 0, 0
            )

            offset = glm.mat4()
            offset[3][2] = 0.001

            P = offset * P
            cheap_shadow_modelling_transformation = V * P * glm.inverse(V)

            cam_mvp = self.camera.P * self.camera.V * cheap_shadow_modelling_transformation
            self.scene.prog_shadow_map['u_mvp'].write(cam_mvp)
            self.scene.prog_shadow_map['u_use_lighting'] = False
            self.scene.prog_shadow_map['u_use_shadow_map'] = False
            self.scene.render_cheap_shadows()
            self.scene.prog_shadow_map['u_use_lighting'] = True
            self.scene.prog_shadow_map['u_use_shadow_map'] = self.scene.controls.use_shadow_map
